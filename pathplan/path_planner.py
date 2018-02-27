from rasterio.features import shapes
import rasterio
import pyproj
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as Axes3D
from shapely.ops import transform
from shapely.geometry import shape, LineString, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.wkb import dumps
from utils import load_shapefile, load_altfile, plot_path, read_tif


import json
import math

import time

import sys

wgs84 = pyproj.Proj(init="epsg:4326")

def utm_zone(lat, lon):
    """Determine the UTM zone for a given latitude and longitude.

    Based on http://gis.stackexchange.com/a/13292

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        zone number: UTM zone number lat/lon falls in
        north: bool indicating North/South
    """
    zone = math.floor((lon + 180) / 6.0) + 1

    # Special cases for Norway and Svalbard
    if lat >= 56 and lat < 64 and lon >= 3 and lon < 12:
        zone = 32

    if lat >= 72 and lat < 84:
        if lon >= 0 and lon < 9:
            zone = 31
        elif lon >= 9 and lon < 21:
            zone = 33
        elif lon >= 21 and lon < 33:
            zone = 35
        elif lon >= 33 and lon < 42:
            zone = 37

    return zone, lat > 0


def proj_utm(zone, north):
    """Proj instance for the given zone.

    Args:
        zone: UTM zone
        north: North zone or south zone

    Returns:
        pyproj.Proj instance for the given zone
    """
    ref = "+proj=utm +zone=%d +ellps=WGS84" % zone
    if not north:
        ref += " +south"
    return pyproj.Proj(ref)


def utm_proj(lat, lon):
    """
    Returns the utm_proj for the given lat and lon
    """

    zone, north = utm_zone(lat, lon)
    return proj_utm(zone, north)


def get_vector_from_raster(rasterfile):

    results = None

    with rasterio.drivers():
        with rasterio.open(rasterfile) as src:
            image = src.read(1) # first band
            results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=None, transform=src.affine)))

    return list(results)


def get_shapes_from_vector(vectors):
    alt_dict = {}
    shapes = []

    #lol at the way that works
    lon, lat = vectors[0]['geometry']['coordinates'][0][0]

    proj = utm_proj(lat, lon)

    def transform_to_proj(x, y, z=None):
        return pyproj.transform(wgs84, proj, x, y, z)

    init_time = time.time()
    for vec in vectors:
        shap = transform(transform_to_proj, shape(vec['geometry']))
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

    print("transforming the vectors took {0} seconds".format(time.time() - init_time))

    return shapes, alt_dict



def distance(p1, p2):
    return sum(map(lambda s: (s[0] - s[1])**2, zip(p1, p2)))**.5


# Args:
#   path: (latitude, longitude) tuples
#   strtree: STRtree containing the topology of the area to explore
#   alt_dict: dict mapping shapely wkt to altitude
#   buffer: number representing how close we need to be to intersect
def plan_path(path, strtree, alt_dict, buffer):
    segments = []
    for i in range(1, len(path)):
        segments.append((path[i-1], path[i]))

    print("Built Segments")
    print("segments", segments)

    new_path  = []

    sorting_time = 0
    query_time = 0
    total_time = 0
    intersection_time = 0
    pure_inter_time = 0

    for seg in segments:
        seg_points = []
        init_time = time.time()
        print("Started Segment")
        ls = LineString(seg)
        query_start = time.time()
        intersecting = list(strtree.query(ls))
        query_time += time.time() - query_start

        print("R Tree query returns {0} intersections".format(len(intersecting)))
        inter_start = time.time()
        for inter in intersecting:

            pure_inter_start = time.time()
            intersection = inter.intersection(ls)
            pure_inter_time += time.time() - pure_inter_start
  
            if not intersection.is_empty:
                for coord in intersection.coords:
                    alt = alt_dict[inter.wkt]
                    #d_x =  seg[0][0] - coord[0] 
                    #d_y =  seg[0][1] - coord[1]
                    #norm = (d_x**2 + d_y**2)**.5
                    #d_x = buffer * (d_x / norm)
                    #d_y = buffer * (d_y / norm)
                    d_x = 0
                    d_y = 0

                    seg_points.append((coord[0] + d_x, coord[1] + d_y, alt + buffer))

        intersection_time += time.time() - inter_start 
        sort_start = time.time()
        seg_points = list(sorted(seg_points, key=lambda x: distance(seg[0], x)))
        sorting_time += time.time() - sort_start

        new_path.extend(seg_points)
        this_seg = time.time() - init_time
        print("Finished Segment in {0}".format(this_seg))

    print("Total sorting time {0}".format(sorting_time))
    print("Total intersection time {0}".format(intersection_time))
    print("Total pure intersection time {0}".format(pure_inter_time))
    print("Total query time {0}".format(query_time))

    return new_path

def read_init_path(filepath):
    miss_dict = json.load(open(filepath))

    proj = None

    tups = []
    for wp in miss_dict:
        if proj == None:
            proj = utm_proj(wp['latitude'], wp['longitude'])

        coord = pyproj.transform(wgs84, proj, wp['longitude'], wp['latitude'],0)
        tups.append(coord)

    return tups, proj

def display_path(path, shapes, alt_dict):
    x, y, z = zip(*path)
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    ax.plot(x, y, z)
    plt.show()

#Also does projection
def save_path(filepath, path, proj):
    arr = []
    for lon, lat, alt in path:
        if proj != None:
            lon, lat, alt = pyproj.transform(proj, wgs84, lon, lat, alt)
        new_dict = {'latitude' : lat, 'longitude' : lon, 'altitude' : alt}
        arr.append(new_dict)

    json.dump(arr, open(filepath, 'w'))





if __name__ == '__main__':
    from argparse import ArgumentParser
    import os

    parser = ArgumentParser(description="Generate a path for an Aerial Lidar drone")
    parser.add_argument("path_file", metavar="INPUT", type=str, help="The original path to modify")
    parser.add_argument("shapes", metavar="BARE-EARTH-SHAPES", type=str, help="Shape file for the bare earth")
    parser.add_argument("alt", metavar="BARE-EARTH-ALT", type=str, help="Altitude file for the bare earth")
    parser.add_argument("--canopy-shapes", type=str, help="Shape file for the canopy", required=False)
    parser.add_argument("--canopy-alt", type=str, help="Altitude file for the canopy")
    parser.add_argument("output", metavar="OUT", type=str, help="Filepath to output the generated path to")
    parser.add_argument("buffer", metavar="buffer", type=float, help="amount of space to leave between surface and path in meters")
    parser.add_argument("--bare-earth-geotiff",  type=str, help="Contains the geotiff to generate the files from",  required=False)
    parser.add_argument("--canopy-geotiff",  type=str, help="Contains the geotiff to generate the files from",  required=False)

    args = parser.parse_args()

    miss_waypoints, proj = read_init_path(args.path_file)

    if args.bare_earth_geotiff:

        vectors = get_vector_from_raster(args.geotif)
        be_shapes, be_alt_dict = get_shapes_from_vector(vectors)

        binary = dumps(MultiPolygon(shapes))

        with open("gen/"+args.geotif+".shapes", "wb") as wkb_file:
            wkb_file.write(binary)
        
        with open("gen/"+args.geotif+".alt.json", "w") as alt_dict_file:
            json.dump(alt_dict, alt_dict_file)

    else:
        be_shapes = load_shapefile(args.shapes)
        be_alt_dict = load_altfile(args.alt)

    if args.canopy_shapes and args.canopy_alt and args.canopy_geotiff:
        vectors = get_vector_from_raster(args.geotif)
        be_shapes, be_alt_dict = get_shapes_from_vector(vectors)

        binary = dumps(MultiPolygon(shapes))

        with open("gen/"+args.geotif+".shapes", "wb") as wkb_file:
            wkb_file.write(binary)
        
        with open("gen/"+args.geotif+".alt.json", "w") as alt_dict_file:
            json.dump(alt_dict, alt_dict_file)
    elif args.canopy_shapes and args.canopy_alt:
        be_shapes = load_shapefile(args.shapes)
        be_alt_dict = load_altfile(args.alt)
    elif args.canopy_shapes or args.canopy_alt:
        print("Error: you need to pass both a canopy altitude dict and a canopy shapefile in")
        sys.exit(-1)

        

    tree = STRtree(shapes)

    new_path = plan_path(miss_waypoints, tree, alt_dict, args.buffer)

    save_path(args.output, new_path, proj)
