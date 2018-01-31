from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command, mavutil

import sys
import json
import time

if len(sys.argv) != 3:
    print("Requires arguments for port number and mission file")

print("Connecting on port {0}".format(sys.argv[1]))
connection_string = "tcp:127.0.0.1:{0}".format(sys.argv[1])
print(connection_string)


cmds = []

mission = json.load(open(sys.argv[2]))

for cmd in mission:
    lat = cmd['latitude']
    lon = cmd['longitude']
    alt = cmd['altitude']
    nav_type = cmd['type']
    if nav_type == 'takeoff':
        nav_type = mavutil.mavlink.MAV_CMD_NAV_TAKEOFF
    elif nav_type == 'landing':
        nav_type = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
    else:
        nav_type = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT

    cmd = Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, nav_type, 0, 0, 0, 0, 0, 0, lat, lon, alt)
    cmds.append(cmd)

def save_mission(aFileName):
    """
    Save a mission in the Waypoint file format 
    (http://qgroundcontrol.org/mavlink/waypoint_protocol#waypoint_file_format).
    """
    print("\nSave mission from Vehicle to file: %s" % aFileName)
    #Download mission from vehicle
    #Add file-format information
    output='QGC WPL 110\n'
    #Add home location as 0th waypoint
    home = cmds[0]
    output+="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (0,1,0,16,0,0,0,0,home.x,home.y,home.z,1)
    #Add commands
    for cmd in cmds:
        commandline="%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (cmd.seq,cmd.current,cmd.frame,cmd.command,cmd.param1,cmd.param2,cmd.param3,cmd.param4,cmd.x,cmd.y,cmd.z,cmd.autocontinue)
        output+=commandline
    with open(aFileName, 'w') as file_:
        print(" Write mission to file")
        file_.write(output)

save_mission("test_mission.txt")
