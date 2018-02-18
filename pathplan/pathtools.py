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

    return ((expected - actual)**2).mean()

def calc_errors_with_gen_noise(filepath, metric=mse):
    waypoints = read_path_from_json(filepath)
    noise_pts = gen_noise_points(waypoints)
    return metric(expected=waypoints, actual=noise_pts)




def display_gen_noise_path(waypoints, noise_pts):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(*np.array(waypoints).T, marker='o', color='b')
    ax.plot(*np.array(noise_pts).T, marker='o', color='r')
    plt.show()

def display_gen_noise_path_with_file(filepath):
    waypoints = read_path_from_json(filepath)
    noise_pts = gen_noise_points(waypoints)
    display_gen_noise_path(waypoints, noise_pts)




def main():
    err = calc_errors_with_gen_noise("path.json", metric=mse)
    print("MSE={}".format(err))

    display_gen_noise_path_with_file("path.json")

# Uncomment to test
# if __name__ == "__main__":
#     main()