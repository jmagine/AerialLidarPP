'''
Contains all methods for evaluating the performance of a path
'''
import sys, time, os, struct, json, fnmatch
from utils import load_shapefile, load_altfile
from shapely.geometry import LineString, Polygon
from shapely.strtree import STRtree
import numpy as np

import types


'''
Returns a list of LineStrings indicating the sections of the
path that intersect with the digital surface map
'''
def calculate_intersections(path, rtree, alts, buf=0):
    intersected = []
    ls = LineString(path)
    tile = rtree.query(ls)
    for pot in tile:
        inter = pot.intersection(ls)
        if not inter.is_empty:
            alt = alts[inter.wkt] + buf
            for x,y,z in inter.coords:
                if z <= alt:
                    intersected.append(inter)
                    break
    return intersected
          

def generator_to_list(array):
    if isinstance(array, types.GeneratorType):
        return list(array)
    return array

def to_np_array(array):
    if not isinstance(array, np.ndarray):
        return np.array(array)
    return array



def read_path_from_json(filepath):
    to_xyz = lambda pt: (pt['longitude'], pt['latitude'], pt['altitude'])
    points = json.load(open(filepath))
    return map(to_xyz, points)

def default_noise(val):
    return val + np.random.normal(0, 0.000035)

def gen_noise_points(waypoints, noise=default_noise):
    add_noise = lambda x, y, z: (noise(x), noise(y), noise(z))
    return map(lambda xyz: add_noise(*xyz), waypoints)

def gen_noise_points_from_file(filepath):
    waypoints = read_path_from_json(filepath)
    return gen_noise_points(waypoints)




def mse(expected, actual):
    """
    Mean squared error of expected and actual waypoints.
    Args:
        expected - A list/generator/np-array of planned waypoints.
        actual - The list/generator/np-array of points that we flew to.
    Returns:
        The mean squared error
    """
    expected = to_np_array(generator_to_list(expected))
    actual = to_np_array(generator_to_list(actual))

    return ((expected - actual)**2).mean(axis=0) # avg along columns

def calc_errors_with_gen_noise(filepath, metric=mse):
    waypoints = read_path_from_json(filepath)
    noise_pts = gen_noise_points(waypoints)
    return metric(expected=waypoints, actual=noise_pts)
