"""
Utility functions to allow for computing MSE of expected and actual waypoints
of the path when running through simulation or in real time. This file also
includes functions to add noise to waypoints to test. For example, the
default noise function over a mean of 0 and a std of 1 will give a MSE of
around 1 usually.

NOTE: This file uses Generators, Lists, Numpy Arrays interchangely, but
will do conversions from generators to lists to numpy arrays if necessary.
"""
from mpl_toolkits.mplot3d import Axes3D

import matplotlib.pyplot as plt
import numpy as np
import json

import types


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

def default_noise(val=0):
    return val + np.random.normal(0, 1.2)

def gen_noise_points(waypoints, noise=default_noise):
    # For each point in waypoints, generate a new line perpendicular to it
    # using point[i] and point[i+1] as the line. Having this line, select
    # randomly one of the nonzero values on this line and add it to the 
    # original point[i] to generate a new point in space.

    UP = np.array([0, 0, 1]) # altitude is stored in z-coordinate

    waypoints = map(lambda pt: np.array(pt), waypoints)
    past_point = next(waypoints)

    for pt in waypoints:
        line = pt - past_point
        perpendicular = np.cross(line, UP)
        noise_line = perpendicular * noise()
        yield noise_line + past_point
        past_point = pt

    yield past_point

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
    waypoints = list(read_path_from_json(filepath))
    noise_pts = list(gen_noise_points(waypoints))
    return metric(expected=waypoints, actual=noise_pts)




def display_gen_noise_path(waypoints, noise_pts):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(*np.array(waypoints).T, marker='o', color='b')
    ax.plot(*np.array(noise_pts).T, marker='o', color='r')
    plt.show()

def display_gen_noise_path_with_file(filepath):
    waypoints = list(read_path_from_json(filepath))
    noise_pts = list(gen_noise_points(waypoints))
    display_gen_noise_path(waypoints, noise_pts)




def main():
    err = calc_errors_with_gen_noise("path.json", metric=mse)
    print("MSE={}".format(err))

    display_gen_noise_path_with_file("path.json")

# Uncomment to test
if __name__ == "__main__":
    main()