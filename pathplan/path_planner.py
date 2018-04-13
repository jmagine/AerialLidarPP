import rasterio
import pyproj
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as Axes3D

from shapely.ops import transform
from shapely.geometry import shape, LineString, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.wkb import dumps

from pathplan.utils import read_init_path, distance
from pathplan.path_planner_numpy import smooth_line
from pathplan.smoothing import concavity_smooth


import json
import math

import time

import sys

#returns true if concave up
def determine_concavity(p1, p2, last_slope):
    dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**.5
    alt_change = p2[2] - p1[2]
    slope = alt_change / dist

    return slope - last_slope > 0, slope

def bleh(path):
    concave_up = []
    concave_down = []

    concave_up_run = None

    p1 = path[0]
    p2 = path[1]

    dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**.5
    alt_change = p2[2] - p1[2]

    last_slope = alt_change / dist 

    last_point = p2

    start = p1

    max_height = max(p1[2], p2[2])

    max_point = p1 if max_height == p1[2] else p2
  
    new_points = []
    for point in path[2:]:
        new_concavity, last_slope = determine_concavity(last_point, point, last_slope)

        if new_concavity != concave_up_run and concavity != None:
            #if concave_up_run:
            #    pass
            #else:
            start_x, start_y, start_z = start
            max_x, max_y, max_z = max_point
            max_x, max_y, max_z = max_point
            new_points.append(start)
            new_points.append((start_x, start_y, max_z))
            new_points.append((max_x, maxy, max_z))
            new_points.append((last_point[0], last_point[1], max_z))
            new_points.append(last_point)

            max_height = point[2]
            start = point
        else:
            max_height = max(point[2], max_height)
        
        concavity = new_concavity
        last_point = point

    return new_points
        
        
        
        

def get_intersection_map(strtree, alt_dict, segment, buf):
    print(segment)
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

from functools import reduce

def project_along_line(dist, p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    norm = (dx**2 + dy**2)**.5
    dx = (dx / norm) * (dist)
    dy = (dy / norm) * (dist)
    return (p2[0] + dx, p2[1] + dy)

def handle_canyon(line1, alt0, alt1, alt2, min_speed, climb_rate, descent_rate, target_speed):
    descent_time = (alt0 - alt1) * descent_rate
    ascent_time = (alt2 - alt1) * climb_rate
    total_time = descent_time + ascent_time
    target_time = line1.length / target_speed

    if target_time >= descent_time:
        new_start = project_along_line(descent_time * target_speed, line1.coords[0],line1.coords[1])
        new_end = project_along_line(ascent_time * target_speed, line1.coords[0],line1.coords[1])
        return LineString([new_start, new_end])

    target_speed = line1.length / (ascent_time + descent_time)
    if target_speed > min_speed:
        new_start = project_along_line(descent_time * target_speed, line1.coords[0],line1.coords[1])
        new_end = project_along_line(ascent_time * target_speed, line1.coords[0],line1.coords[1])
        return LineString([new_start, new_end])

    return None
    
    
def handle_two_lines(line1, line2, alt1, alt2, min_speed, target_speed, climb_rate, descent_rate):
    vert_dist = abs(alt2 - alt1)
    #ascent
    if alt2 > alt1:
        time = vert_dist / climb_rate
        horiz = target_speed * time
        if horiz < line1.length:
            new_end = project_along_line(horiz, line1.coords[0],line1.coords[1])
            return (LineString([line1.coords[0], (new_end[0], new_end[1], 0)]), alt1), (line2, alt2)  
        else:
            max_speed = line1.length / time
            if max_speed > min_speed:
                new_end = project_along_line(line1.length, line1.coords[1], line1.coords[0])
                line1 = LineString([line1.coords[0], (new_end[0], new_end[1], 0)])
                return (line1, alt1), (line2, alt2)
            else:
                return (None, alt2), (line2, alt2)
    #descent
    else:
        time = vert_dist / descent_rate
        horiz = target_speed * time
        if horiz < line2.length:
            new_start = project_along_line(horiz, line2.coords[1],line2.coords[0])
            return ((line1, alt1), (LineString([(new_start[0], new_start[1], 0), line2.coords[1]]), alt2))
        else:
            max_speed = line2.length / time
            if max_speed > min_speed:
                new_start = project_along_line(line2.length, line2.coords[1], line2.coords[0])
                line2 = LineString([(new_start[0], new_start[1], 0), line1.coords[1]])
                return (line1, alt1), (line2, alt2)
            else:
                return (line1, alt1), (None, alt1)

def adjust_speed(lines, smooth_dict, min_speed, target_speed, climb_rate, descent_rate):
    new_lines = []
    line1 = lines.pop(0)
    line2 = lines.pop(0)
    alt1 = smooth_dict[line1.wkt]
    alt2 = smooth_dict[line2.wkt]

    while len(lines) > 0:

        print(len(lines))

        vert_dist = abs(alt2 - alt1)
        #descent
        if alt1 > alt2:
            (l1, a1), (l2, a2) = handle_two_lines(line1, line2, alt1, alt2, min_speed, target_speed, climb_rate, descent_rate)

            if l2 == None:
                popped = lines.pop(0)
                line2 = LineString(line2.coords[1], popped.coords[1])
                alt2 = smooth_dict[popped.wkt]
            else:
                new_lines.append(l1)
                smooth_dict[l1.wkt] = a1
                line1 = l2
                line2 = lines.pop(0)

                alt1 = alt2
                alt2 = smooth_dict[line2.wkt]

        #ascent
        else:
            (l1, a1), (l2, a2) = handle_two_lines(line1, line2, alt1, alt2, min_speed, target_speed, climb_rate, descent_rate)

            if l1 == None:
                time = abs(alt1-alt2) / climb_rate
                accum_len = line1.length
                max_speed = line1.length / time
                while max_speed < min_speed:
                    back = new_lines.pop()
                    last_acc = accum_len
                    accum_len += back.length
                    max_speed = accum_len / time
                line1 = line2
                line2 = lines.pop(0)
            else:
                new_lines.append(l1)
                smooth_dict[l1.wkt] = a1
                line1 = line2
                line2 = lines.pop(0)
                alt1 = alt2
                alt2 = smooth_dict[line2.wkt]

    return new_lines, smooth_dict
            


def smooth_segments(start, segments, seg_dict, min_length):
    print("smoothing a segment", min_length)
    sorted_segs = list(sorted(segments, key=lambda x: distance(start, x.coords[0])))
    smooth_dict = dict(seg_dict)

    #This is dumb
    def reducer(acc, nxt):

        master_list, accum_list, dist = acc
        
        accum_list.append(nxt)
        total_dist = nxt.length + dist
        if total_dist >= min_length:
            start_coord = accum_list[0].coords[0]

            if total_dist >= min_length:
                #dx = line.coords[1][0] - line.coords[0][0]
                #dy = line.coords[1][1] - line.coords[0][1]
                #norm = (dx**2 + dy**2)**.5
                #dx = (dx / norm) * (min_length - dist)
                #dy = (dy / norm) * (min_length - dist)
                #end_coord = (line.coords[0][0] + dx, line.coords[0][1] + dy, 0)
                end_coord = nxt.coords[-1]
                ls = LineString([start_coord, end_coord])
                smooth_dict[ls.wkt] = max([smooth_dict[x.wkt] for x in accum_list])

                master_list.append(ls)
                accum_list = []
                dist = 0
                #remainder = LineString([end_coord, line.coords[1]])
                #smooth_dict[remainder.wkt] = smooth_dict[line.wkt]

                #accum_list.clear()
                #if remainder.length >= min_length:
                #    master_list.append(remainder)
                #    dist = 0
                #    assert len(accum_list) == 0
                #elif remainder.length > 0:
                #    accum_list.append(remainder)
                #    assert len(accum_list) == 1
                #    dist = remainder.length
        else:
            accum_list.append(nxt)
            dist += nxt.length

        return master_list, accum_list, dist    

    (smooth_lines, accum, _) = tuple(reduce(reducer, sorted_segs, ([], [], 0)))
    if len(accum) > 0:
        smooth_lines.append(LineString([accum[0].coords[0], accum[-1].coords[1]]))
        smooth_dict[smooth_lines[-1].wkt] = max([smooth_dict[x.wkt] for x in accum]) 
    return smooth_lines, smooth_dict

def lines_to_coords(lines, smooth_dict):
    coords = []

    for line in lines:
        for (x,y,z) in line.coords:
            coords.append((x, y, smooth_dict[line.wkt]))

    return coords

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

def account_for_speed(path, horiz_speed, descent_rate, climb_rate):
    new_path = []
    last = path[0]

    for p in path[1:]:
        last_alt = last[2]
        alt = p[2]

        dist = ((p[0]-last[0])**2 + (p[1] - last[1])**2)**.5

        #climb
        if last_alt < alt:
            time = abs(last_alt - alt) / climb_rate
            horiz_dist = time * horiz_speed
            if horiz_dist < dist:
                pass   
        #descent
        else:
            time = abs(last_alt - alt) / descent_rate
            horiz_dist = time * horiz_speed

        


# Args:
#   path: (latitude, longitude) tuples
#   strtree: STRtree containing the topology of the area to explore
#   alt_dict: dict mapping shapely wkt to altitude
#   buffer: number representing how close we need to be to intersect
def plan_path(path, strtree, alt_dict, be_buffer, obs_buffer, min_alt_change, climb_rate, descent_rate, speed, canopy_strtree=None, canopy_alt_dict=None):
    segments = []
    min_height = be_buffer
    print(path)
    for i in range(1, len(path)):
        segments.append((path[i-1], path[i]))

    #print("Built Segments")
    #print("segments", segments)

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
        #print("Started Segment")
        init_time = time.time()
        lines, int_dict = get_intersection_map(strtree, alt_dict, seg, be_buffer)

        for (key, val) in int_dict.items():
            super_int_dict[key] = val - be_buffer

        if canopy_strtree != None and canopy_alt_dict != None:
            canopy_dict, can_lineds = get_intersection_map(canopy_strtree, canopy_alt_dict, seg, canopy_buffer)
            int_dict, lines = resolve_two_dicts(can_lines, lines, canopy_dict, int_dict) 

        obs_for_graph.extend(list(sorted(lines, key=lambda x:distance(seg[0], x.coords[0]))))
        lines, smooth_dict = smooth_segments(seg[0], lines, int_dict, min_alt_change)

        print(lines)

        #lines, smooth_dict = adjust_speed(lines, smooth_dict, min_speed, max_speed, climb_rate, descent_rate)

        points = []
        for line in lines:
            z = smooth_dict[line.wkt]
            x2,y2,_ = line.coords[-1]
            x1,y1,_ = line.coords[0]
            points.append((x1, y1, z))
            points.append((x2, y2, z))

        new_path.extend(points)

    new_obs = []
    for line in obs_for_graph:
        new_obs.append((line.coords[0][0], line.coords[0][1], super_int_dict[line.wkt]))
        new_obs.append((line.coords[1][0], line.coords[1][1], super_int_dict[line.wkt]))
    #print(new_path)
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
