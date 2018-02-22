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

if __name__ == '__main__':
    from argparse import ArgumentParser
    import os
    import glob

    parser = ArgumentParser(description="Converts a folder containing a list of BIN files into one flight path")
    parser.add_argument("logs", metavar="DIR", type=str, help="Folder containing all of the bin files")

    args = parser.parse_args()

    path = []

    def key_fun(filename):
        return int(os.path.splitext(os.path.basename(filename))[0])

    files = list(sorted(glob.glob(args.logs+"/*.BIN"), key=key_fun))
    
    for binfile in files:
        new_path = load_path_from_bin(binfile)
        path.extend(new_path)

    import json
    json.dump(path, open(args.logs+"/../" + "flighttest1.flight.json", "w"))
