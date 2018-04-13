from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command, mavutil

import sys
import json
import time
import math
import os
import shutil as sh

try:
    from pymavlink.mavextra import *
except:
    print("WARNING: Numpy missing, mathematical notation will not be supported..")

import inspect

from pymavlink import mavutil

# Input should be a .BIN file in the qgroundcontrol format
# Outputs an array of dictionaries each containing the packet data
def parse_dataflash_log(filename, planner=False, notimestamps=False,
        robust=True, dialect='ardupilotmega', zero_time_base=False,
        types=None, nottypes=None, csv_sep=',', format=None, follow=False,
        parms=False, nobaddata=True, show_source=True, showseq=True,
        source_system=None, source_component=None, link=None, condition=None):
    '''
    mlog = mavutil.mavlink_connection(filename, planner_format=planner,
                                      notimestamps=notimestamps,
                                      robust_parsing=robust,
                                      dialect=dialect,
                                      zero_time_base=zero_time_base)
    '''
    mlog = mavutil.mavlink_connection(filename)

    ext = os.path.splitext(filename)[1]
    isbin = ext in ['.bin', '.BIN']

    output = []
    # Keep track of data from the current timestep. If the following timestep has the same data, it's stored in here as well. Output should therefore have entirely unique timesteps.
    while True:
        m = mlog.recv_match(blocking=follow)
        if not m:
            # FIXME: Make sure to output the last CSV message before dropping out of this loop
            break

        mdict = m.to_dict()
        mdict['timestamp'] = m._timestamp
        output.append(mdict)

    return output

def load_path_from_bin(filename):
    parsed_log = parse_dataflash_log(filename)
    gps_points = [{'latitude':x['Lat'],'longitude':x['Lng'], 'altitude':x['Alt']}  for x in parsed_log if x['mavpackettype'] == 'GPS']
    return gps_points

import glob
def parse_bins(logs):
    def key_fun(filename):
        return int(os.path.splitext(os.path.basename(filename))[0])

    files = list(sorted(glob.glob(logs+"/*.BIN"), key=key_fun))
    
    path = []
    for binfile in files:
        new_path = load_path_from_bin(binfile)
        path.extend(new_path)

    return path

def get_command_list(mission, tif):

    home_pos_alt = mission[0]
    raster = rasterio.open(tif)

    raster_proj = pyproj.Proj(raster.crs, preserve_units=True)

    lat = mission[0]['latitude']
    lon = mission[0]['longitude']

    proj = utm_proj(32.989613, -117.128693)
    lon,lat = pyproj.transform(wgs84, raster_proj, lon, lat)

    print(lon,lat)
    row, col = raster.index(lon, lat)

    print(row, col)

    data = raster.read()[0,:,:]
    home_pos_alt = data[row][col] * .3048

    nav_type = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
    cmd = Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, nav_type, 0, 0, 0, 0, 0, 0, lat, lon, 20)

    cmds = [cmd]

    
    for cmd in mission:
        lat = cmd['latitude']
        lon = cmd['longitude']
        #lat,lon,alt = cmd
        #lon, lat = pyproj.transform(proj, wgs84, lat, lon)
        #nav_type = cmd['type']
        #if nav_type == 'takeoff':
        #    nav_type = mavutil.mavlink.MAV_CMD_NAV_TAKEOFF
        #elif nav_type == 'landing':
        #    nav_type = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
        #else:

        nav_type = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
    
        cmd = Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, nav_type, 0, 0, 0, 0, 0, 0, lat, lon, home_pos_alt + 20)
        cmds.append(cmd)

    return cmds

def fly(port, missionfile, logdir):
    time.sleep(10)
    
    
    print("Connecting on port {0}".format(port))
    connection_string = "tcp:127.0.0.1:{0}".format(port)
    print(connection_string)
    
    print("connecting")
    vehicle = connect(connection_string, wait_ready=True)
    print("finished connecting")
    
    vehicle.parameters['ARMING_CHECK'] = 0
    
    cmds = vehicle.commands
    
    cmds.clear()
    
    mission = json.load(open(missionfile))
    
    
    cmds.upload()
    
    def arm_and_takeoff(aTargetAltitude):
        """
        Arms vehicle and fly to aTargetAltitude.
        """
    
        print("Basic pre-arm checks")
        # Don't let the user try to arm until autopilot is ready
        while not vehicle.is_armable:
            print(" Waiting for vehicle to initialise...")
            time.sleep(1)
    
    
        print("Arming motors")
        # Copter should arm in GUIDED mode
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
    
        while not vehicle.armed:      
            print(" Waiting for arming...")
            time.sleep(1)
    
        print("Taking off!")
        vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude
    
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
        #  after Vehicle.simple_takeoff will execute immediately).
        while True:
            print(" Altitude: ", vehicle.location.global_relative_frame.alt)
            if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: #Trigger just below target alt.
                print("Reached target altitude")
                break
            time.sleep(1)
    
    target_alt = mission[0]['altitude']
    arm_and_takeoff(target_alt)
    
    #vehicle.commands.next=0
    
    # Set mode to AUTO to start mission
    vehicle.mode = VehicleMode("AUTO")
    
    def get_location_metres(original_location, dNorth, dEast):
        """
        Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the 
        specified `original_location`. The returned Location has the same `alt` value
        as `original_location`.
    
        The function is useful when you want to move the vehicle around specifying locations relative to 
        the current vehicle position.
        The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
        For more information see:
        http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
        """
        earth_radius=6378137.0 #Radius of "spherical" earth
        #Coordinate offsets in radians
        dLat = dNorth/earth_radius
        dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))
    
        #New position in decimal degrees
        newlat = original_location.lat + (dLat * 180/math.pi)
        newlon = original_location.lon + (dLon * 180/math.pi)
        return LocationGlobal(newlat, newlon,original_location.alt)
    
    
    def get_distance_metres(aLocation1, aLocation2):
        """
        Returns the ground distance in metres between two LocationGlobal objects.
    
        This method is an approximation, and will not be accurate over large distances and close to the 
        earth's poles. It comes from the ArduPilot test code: 
        https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
        """
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5
    
    
    
    def distance_to_current_waypoint():
        """
        Gets distance in metres to the current waypoint. 
        It returns None for the first waypoint (Home location).
        """
        nextwaypoint = vehicle.commands.next
        if nextwaypoint==0:
            return None
        missionitem=vehicle.commands[nextwaypoint-1] #commands are zero indexed
        lat = missionitem.x
        lon = missionitem.y
        alt = missionitem.z
        targetWaypointLocation = LocationGlobalRelative(lat,lon,alt)
        distancetopoint = get_distance_metres(vehicle.location.global_frame, targetWaypointLocation)
        return distancetopoint
    
    while True:
        nextwaypoint=vehicle.commands.next
        print('Distance to waypoint (%s): %s' % (nextwaypoint, distance_to_current_waypoint()))
        if nextwaypoint == len(mission)-1: 
            print("Exit 'standard' mission when start heading to final waypoint ({0})".format(len(mission)))
            break

    sh.move("{0}/{1}".format(os.getcwd(), "logs"), logdir)
    os.remove("eeprom.bin")
    sh.rmtree("terrain")
    
    return logdir

def save_mission(aFileName, cmds):
    """
    Save a mission in the Waypoint file format (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
    """
    output='QGC WPL 110\n'
    for cmd in cmds:
        commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
        output+=commandline
    with open(aFileName, 'w') as file_:
        file_.write(output)

import sys
from os.path import splitext, basename
if __name__ == '__main__':
    import rasterio
    import pyproj
    from geo import wgs84, utm_proj
    if len(sys.argv) != 3:
        print("need a tiffile and a path file")
        sys.exit()

    tiffile = sys.argv[1]
    missionfile = sys.argv[2]
    mission = json.load(open(missionfile))

    filename = "{0}.txt".format(basename(splitext(missionfile)[0]))

    cmds = get_command_list(mission, tiffile)
    save_mission(filename,cmds)
