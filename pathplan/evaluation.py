'''
Dumps a Mavlink log file.
Input file should be a ".BIN" file in the format that qgroundcontrol uses,
which consists of a series of MAVLink packets, each with a 64 bit timestamp
header. The timestamp is in microseconds since 1970 (unix epoch).
'''
import sys, time, os, struct, json, fnmatch
from utils import load_shapefile, load_altfile
from shapely.geometry import LineString, Polygon
from shapely.strtree import STRtree
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as Axes3D
from path_planner_numpy import read_tif


def evaluate_path(path, rtree, alts):
    intersected = []
    ls = LineString(path)
    tile = rtree.query(ls)
    for pot in tile:
        inter = pot.intersection(ls)
        if not inter.is_empty:
            alt = alts[inter.wkt]
            for x,y,z in inter.coords:
                if z <= alt:
                    intersected.append(inter)
                    break
    return intersected
          

def evaluate_path_with_buffer(path, rtree, alts, buffer):
    ls = LineString(path)
    inters = rtree.query(ls.buffer(buffer))

def plot_path(surface, *paths):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for path in paths:
        x, y, z = zip(*path)
        ax.plot(x, y, z)


    surf_x, surf_y, surf_z = zip(*surface)
    ax.plot_surface(surf_x, surf_y, surf_z)

    plt.show()
    

#TODO Come up with a good way to analyze the deviation between the generated and the flown path
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Compares a several paths to each other")

    parser.add_argument("geotiff", metavar="TIF", type=str, help="Tif file")
    parser.add_argument("paths", metavar="PATH", nargs='+', type=str, help="List of path json files to compare ")

    args = parser.parse_args()



    paths = []

    for path in args.paths:
        paths.append(json.load(open(path)))
 
    surface = read_tif(args.geotiff)

    plot_path(surface, *paths)

