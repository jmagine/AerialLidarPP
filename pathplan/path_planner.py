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


def get_shapes_from_vector(vectors, do_transform=True):
    alt_dict = {}
    shapes = []

    #lol at the way that works
    lon, lat = vectors[0]['geometry']['coordinates'][0][0]

    proj = utm_proj(lat, lon)

    def transform_to_proj(x, y, z=None):
        return pyproj.transform(wgs84, proj, x, y, z)

    init_time = time.time()
    for vec in vectors:
        shap = shape(vec['geometry'])
        if do_transform:
            shap = transform(transform_to_proj, shap)
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

    print("transforming the vectors took {0} seconds".format(time.time() - init_time))

    return shapes, alt_dict



def distance(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**.5

def get_intersection_map(strtree, alt_dict, segment, buf):
    ls = LineString(segment)
    query_start = time.time()
    intersecting = list(strtree.query(ls))
    #query_time += time.time() - query_start
 
    print("R Tree query returns {0} intersections".format(len(intersecting)))
    inter_start = time.time()
    int_dict = {}
    lines = []
    for inter in intersecting:
 
        pure_inter_start = time.time()
        intersection = inter.intersection(ls)
        #pure_inter_time += time.time() - pure_inter_start
 
        if not intersection.is_empty:
           alt = alt_dict[inter.wkt]
           int_dict[intersection.wkt] = alt + buf
           lines.append(intersection)
 
    return lines, int_dict

def smooth_segments(start, segments, seg_dict, min_change):
    sorted_segs = list(sorted(segments, key=lambda x: distance(start, x.coords[0])))
    smooth_dict = dict(seg_dict)

    #This is dumb
    def reducer(acc, nxt):
        curr_alt = smooth_dict[acc[-1].wkt]
        nxt_alt = smooth_dict[nxt.wkt]
        if abs(curr_alt -  nxt_alt) < min_change:
            
            del smooth_dict[acc[-1].wkt]

            acc[-1] = LineString([acc[-1].coords[0], nxt.coords[-1]])
            smooth_dict[acc[-1].wkt] = max(curr_alt, nxt_alt)
        else:
            acc.append(nxt)
            smooth_dict[nxt.wkt] = nxt_alt
        return acc    

    return reduce(reducer, sorted_segs[1:], [sorted_segs[0]]), smooth_dict

def resolve_two_dicts(canopies, lines, canopy_dict, int_dict):
    canopy = STRtree(list(canopies))
    new_dict = {}
    new_segs = []
    for line in lines:
       queried = canopy.query(line)
       
       for inter in queried:
           intersection = inter.intersection(ls)

           if not intersection.is_empty:
              alt1 = canopy_dict[inter.wkt]
              alt2 = int_dict[line.wkt]
              int_dict[intersection.wkt] = max(alt1, alt2)
              new_segs.append(intersection)

    return new_segs, new_dict
        

   

# Args:
#   path: (latitude, longitude) tuples
#   strtree: STRtree containing the topology of the area to explore
#   alt_dict: dict mapping shapely wkt to altitude
#   buffer: number representing how close we need to be to intersect
def plan_path(path, strtree, alt_dict, be_buffer, obs_buffer, min_alt_change, climb_rate, descent_rate, max_speed, canopy_strtree=None, canopy_alt_dict=None):
    segments = []
    print(path)
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

    last_seg = None

    obs_for_graph = []

    super_int_dict = {}

    for seg in segments:
        print("Started Segment")
        init_time = time.time()
        lines, int_dict = get_intersection_map(strtree, alt_dict, seg, be_buffer)

        for (key, val) in int_dict.items():
            super_int_dict[key] = val - be_buffer

        if canopy_strtree != None and canopy_alt_dict != None:
            canopy_dict, can_lineds = get_intersection_map(canopy_strtree, canopy_alt_dict, seg, canopy_buffer)
            int_dict, lines = resolve_two_dicts(can_lines, lines, canopy_dict, int_dict) 

        obs_for_graph.extend(list(sorted(lines, key=lambda x:distance(seg[0], x.coords[0]))))
        lines, smooth_dict = smooth_segments(seg[0], lines, int_dict, min_alt_change)

        points = [(lines[0].coords[0][0], lines[0].coords[0][1], smooth_dict[lines[0].wkt], max_speed)]
        for i in range(1,len(lines)):
            prev = lines[i-1]
            curr = lines[i]
            last_alt = smooth_dict[prev.wkt]
            curr_alt = smooth_dict[curr.wkt]
            horiz = calculate_horiz_dist(curr_alt, last_alt, climb_rate, descent_rate, max_speed)

            print horiz

            mid = prev.coords[1]

            speed = max_speed
            if last_alt > curr_alt:
                #We need to descent, so we project at the curr altitude
                other = curr.coords[1]
                dx, dy = vec_sub(other, mid) 

                projected = vec_add(mid, (horiz * dx, horiz * dy))


                if horiz > curr.length:
                    horiz = curr.length 
                    speed = horiz / (abs(last_alt - curr_alt) / descent_rate )

                points.append((mid[0], mid[1], last_alt, speed))
                points.append((projected[0], projected[1], curr_alt, max_speed))
            else:
                #We need to ascend, so we project at the last altitude
                other = prev.coords[0]
                dx, dy = vec_sub(other, mid) 
                projected = vec_add(mid, (horiz* dx, horiz* dy))

                if horiz > prev.length:
                    horiz = prev.length 
                    speed = horiz / (abs(last_alt - curr_alt) / descent_rate )

                points.append((projected[0], projected[1], last_alt, speed))
                points.append((mid[0], mid[1], curr_alt, max_speed))

        last_alt = smooth_dict[lines[-1].wkt]
        points.append((lines[-1].coords[1][0], lines[-1].coords[1][1], last_alt, max_speed))
        new_path.extend(points)

    new_obs = []
    for line in obs_for_graph:
        new_obs.append((line.coords[0][0], line.coords[0][1], super_int_dict[line.wkt]))
        new_obs.append((line.coords[1][0], line.coords[1][1], super_int_dict[line.wkt]))
    print(new_path)
    return new_path, new_obs

def vec_sub(first, second):
    dx = first[0] - second[0]
    dy = first[1] - second[1]

    norm = (dx**2 + dy**2)**.5

    return dx / norm, dy / norm

def vec_add(first, second):
    dx = first[0] + second[0]
    dy = first[1] + second[1]

    return dx, dy

def calculate_horiz_dist(alt, last_alt, climb_rate, descent_rate, min_speed):
    d_alt = last_alt - alt

    if d_alt < 0:
        d_time = abs(d_alt) / climb_rate
    else:
        d_time = abs(d_alt) / descent_rate
    
    horiz_dist = min_speed * d_time

    return horiz_dist

def generate_points(line, alt, climb_rate, descent_rate, min_speed, last_start):
    if last_start == None:
        return [(line.coords[0][0], line.coords[0][1], alt)] 

    d_alt = last_start[2] - alt

    if d_alt < 0:
        d_time = d_alt / climb_rate
    else:
        d_time = d_alt / descent_rate
    
    horiz_dist = min_speed * d_time

    d_x =  lines.coords[0][0] - last_start[0]
    d_y =  lines.coords[0][1] - last_start[1]
    norm = (d_x**2 + d_y**2)**.5
    d_x = horiz_dist * (d_x / norm)
    d_y = horiz_dist * (d_y / norm)

    

    
    
    

def read_init_path(filepath, proj=None):
    miss_dict = json.load(open(filepath))

    tups = []
    for wp in miss_dict:
        if proj == None:
            proj = utm_proj(wp['latitude'], wp['longitude'])

        coord = pyproj.transform(wgs84, proj, wp['longitude'], wp['latitude'],0)
        if 'altitude' in wp:
            coord = (coord[0], coord[1], wp['altitude'] * 3.28084)
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
        new_dict = {'latitude' : lat, 'longitude' : lon, 'altitude' : alt * .3048, 'speed':0}
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

        with open("gen/"+args.bare_earth_geotiff+".shapes", "wb") as wkb_file:
            wkb_file.write(binary)
        
        with open("gen/"+args.bare_earth_geotiff+".alt.json", "w") as alt_dict_file:
            json.dump(alt_dict, alt_dict_file)

    else:
        be_shapes = load_shapefile(args.shapes)
        be_alt_dict = load_altfile(args.alt)

    canopy_tree = None
    canopy_shapes = None
    canopy_alt_dict = None

    if args.canopy_shapes and args.canopy_alt and args.canopy_geotiff:
        vectors = get_vector_from_raster(args.canopy_geotiff)
        can_shapes, can_alt_dict = get_shapes_from_vector(vectors)

        binary = dumps(MultiPolygon(can_shapes))

        with open("gen/"+args.canopy_geotiff+".shapes", "wb") as wkb_file:
            wkb_file.write(binary)
        
        with open("gen/"+args.canopy_geotiff+".alt.json", "w") as alt_dict_file:
            json.dump(alt_dict, alt_dict_file)
    elif args.canopy_shapes and args.canopy_alt:
        can_shapes = load_shapefile(args.shapes)
        can_alt_dict = load_altfile(args.alt)
    elif args.canopy_shapes or args.canopy_alt:
        print("Error: you need to pass both a canopy altitude dict and a canopy shapefile in")
        sys.exit(-1)

    if canopy_shapes != None:
        canopy_tree = STRtree(canopy_shapes)        

    be_tree = STRtree(be_shapes)

    

    new_path = plan_path(miss_waypoints, be_tree, be_alt_dict, args.buffer, 0, 2, 10,10, 10, 10, canopy_tree, canopy_alt_dict)

    save_path(args.output, new_path, proj)
