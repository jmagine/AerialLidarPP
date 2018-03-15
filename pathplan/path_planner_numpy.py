'''*-----------------------------------------------------------------------*---
                                                          Authors: Jason Ma
                                                          Date   : Feb 11, 2018
    File Name  : path_planner_numpy.py
    Description: Generates path waypoints using numpy. For all images/rasters,
                 it is important to note that this program treats axis 0 as y.
---*-----------------------------------------------------------------------*'''

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from geo import read_tif
from utils import save_path

import json
import numpy as np
from PIL import Image
from math import hypot

'''[Config vars]------------------------------------------------------------'''
#RASTER_FILE = "../tests/images/sine-0.1f-20a.tif"
RASTER_FILE = "../tests/images/ucsd-dsm.tif"
HEIGHT_TO_BARE = 3
HEIGHT_TO_CANOPY = 3
PATH_SPACING = 0.5

'''[gen_path]------------------------------------------------------------------
  Adjusts waypoints as necessary to place them over surface model in raster,
  and then interpolates values between raster.
  
  surface_raster - raster image containing surface map
  waypoints - list of waypoints to hit with path
  return - list of points in x,y,z coordinates representing revised waypoints
----------------------------------------------------------------------------'''
def gen_path(surface_raster, canopy_raster, waypoints):

  #path_points = []
  x_points = []
  y_points = []
  z_points = []

  if len(waypoints) < 2:
    return x_points, y_points, z_points

  for i in range(len(waypoints) - 1):
    x, y, z = gen_segment(surface_raster, canopy_raster, waypoints[i], waypoints[i + 1])
    x_points.extend(x)
    y_points.extend(y)
    z_points.extend(z)
    #path_points.extend(gen_segment(surface_raster, waypoints[i], waypoints[i + 1]))

  return x_points, y_points, z_points

'''[gen_segment]---------------------------------------------------------------
  Creates a segment from the x and y coordinates in the raster.
  
  surface_raster - raster image containing surface map
  wp0 - source waypoint
  wp1 - dest waypoint
  return - list of x, y, z points interpolated between two waypoints
----------------------------------------------------------------------------'''
def gen_segment(surface_raster, canopy_raster, wp0, wp1):
  src_x = wp0[0]
  src_y = wp0[1]

  dest_x = wp1[0]
  dest_y = wp1[1]

  delta_x = dest_x - src_x
  delta_y = dest_y - src_y
  seg_dist = hypot(delta_x, delta_y)

  # Find all points in between src and dest
  # This will be needed when smoothing based on heights!
  #cells = raster_line(wp0, wp1)
  #iterate over points, delete sides if both are lower, repeat if sides deleted

  curr_dist = 0
  x = src_x
  y = src_y

  x_points = []
  y_points = []
  z_points = []
  #points = []

  while curr_dist < seg_dist:
    # calculate avoid height (can also utilize bare earth model in future)
    avoid_height = HEIGHT_TO_BARE
    canopy_avoid = HEIGHT_TO_CANOPY

    # stay the designated height above the surface model
    x_points.append(x)
    y_points.append(y)
    z_points.append(max(surface_raster[int(y)][int(x)] + avoid_height, canopy_raster[int(y)][int(x)] + canopy_avoid))
    #points.append([x, y, surface_raster[int(y)][int(x)] + avoid_height])

    x += delta_x * PATH_SPACING / seg_dist
    y += delta_y * PATH_SPACING / seg_dist
    curr_dist += PATH_SPACING

  # calculate avoid height
  avoid_height = HEIGHT_TO_BARE
  
  x_points.append(dest_x)
  y_points.append(dest_y)
  z_points.append(surface_raster[int(dest_y)][int(dest_x)] + avoid_height)
  #points.append([dest_x, dest_y, surface_raster[int(dest_y)][int(dest_x)] + avoid_height])

  return x_points, y_points, z_points

'''[raster_line]---------------------------------------------------------------
  Find all raster coordinates that are on path between two waypoints
  
  wp0 - source waypoint
  wp1 - dest waypoint
  return - list of coordinates between two waypoints
----------------------------------------------------------------------------'''
def raster_line(wp0, wp1):

  # start and end coords
  src_x = wp0[0]
  src_y = wp0[1]

  dest_x = wp1[0]
  dest_y = wp1[1]

  # deltas
  dx = dest_x - src_x
  dy = dest_y - src_y

  # sign of movement
  sx = -1 if src_x > dest_x else 1
  sy = -1 if src_y > dest_y else 1

  dx = abs(dx)
  dy = abs(dy)
  
  points = []

  x = src_x
  y = src_y

  ix = 0
  iy = 0

  points.append([x, y])

  while ix < dx or iy < dy:
    # horizontal step
    if (ix + 0.5) / dx < (iy + 0.5) / dy:
      x += sx
      ix += 1
    # vertical step
    else:
      y += sy
      iy += 1
    points.append([x, y])

  return points

'''[smooth_line]---------------------------------------------------------------
  Smoothes a list of point tuples by gradually changing height for sharp
  height changes. The output should also be able to avoid the same obstacles
  that the original path avoids.

  points - original points list
  max_height_diff - max height diff that can occur between two points
  return - list of smoothed points
----------------------------------------------------------------------------'''
def smooth_line(points, max_height_diff):

  #determine peaks of height list and calculate slopes to last peak
  # start at end slope and iterate backwards,
  #   for any slope that is greater than desired, correct heights forwards

  new_points = []
  new_points.extend(points)
  peaks = []
  peak_inds = []
  slopes = []

  #init state
  #last_peak = 0
  going_up = False
  peaks.append(points[0])
  peak_inds.append(0)

  for i in range(1, len(points) - 1):
    z = points[i]
    #going up
    if z > points[i - 1]:
      #last peak is not actually peak
      if going_up:
        peaks.pop()
        peak_inds.pop()
        peaks.append(points[i])
        peak_inds.append(i)
        #last_peak = i
      else:
        going_up = True
        peaks.append(points[i])
        peak_inds.append(i)
        #last_peak = i
    #going down
    elif z < points[i - 1]:
      going_up = False

  peaks.append(points[len(points) - 1])
  peak_inds.append(len(points) - 1)
  
  print("Peaks:", peaks)
  print("Peak Inds:", peak_inds)
  
  #peaks seems pretty useless actually...
  for i in range(1, len(peaks)):
    slope = (peaks[i] - peaks[i - 1]) / (peak_inds[i] - peak_inds[i - 1])
    slopes.append(slope)
  
  print("Slopes:", slopes)
  
  #TODO fix case: flat area followed by neg slope. Flat area not decreasing in altitude, even though slope assumes start is at start of flat area
  # smooth negative slopes
  for i in range(len(slopes)):
    if slopes[i] >= 0:
      continue

    peak_ind_0 = peak_inds[i]
    peak_ind_1 = peak_inds[i + 1]

    for j in range(peak_ind_0 + 1, peak_ind_1 + 1):
      #make all points on this slope neg max_height_diff
      if slopes[i] < max_height_diff * -1:
        #ensure this point is still above terrain
        if new_points[j - 1] - max_height_diff > new_points[j]:
          new_points[j] = new_points[j - 1] - max_height_diff
      else:
        #ensure this point is still above terrain
        if new_points[j - 1] + slopes[i] > new_points[j]:
          new_points[j] = new_points[j - 1] + slopes[i]

  
  # smooth positive slopes
  for i in reversed(range(len(slopes))):
    if slopes[i] < 0:
      continue

    peak_ind_0 = peak_inds[i]
    peak_ind_1 = peak_inds[i + 1]
    #print(peak_ind_0, peak_ind_1)

    for j in reversed(range(peak_ind_0, peak_ind_1)):
      #make all points on this slope max_height_diff
      if slopes[i] > max_height_diff:
        #ensure this point is still above terrain
        if new_points[j + 1] - max_height_diff > new_points[j]:
          new_points[j] = new_points[j + 1] - max_height_diff
      else:
        #ensure this point is still above terrain
        if new_points[j + 1] - slopes[i] > new_points[j]:
          new_points[j] = new_points[j + 1] - slopes[i]
  
  return new_points

  
import rasterio
import pyproj
def plan_path(init_waypoints, bare_earth, canopy,  smoothing_params=[10, 0.5]):
  #[TODO] read waypoints from file
  #waypoints = [(0,0), (199, 199), (0, 199), (199, 0)]

  raster = rasterio.open(bare_earth)

  raster_proj = pyproj.Proj(raster.crs)

  raster_width = abs(raster.bounds.right - raster.bounds.left)
  raster_height = abs(raster.bounds.top - raster.bounds.bottom)
 

  waypoints = []

  for waypoint in init_waypoints:
    x = int((abs(waypoint[0] - raster.bounds.bottom) / raster_height) * raster.height)
    y = int((abs(waypoint[1] - raster.bounds.left) / raster_width) * raster.width)
    waypoints.append((x, y))


  print(waypoints)
  #[DEBUG]
  #plt.imshow(image)
  #plt.show()
  
  image = read_tif(bare_earth)
  print(image)
  print(image.shape)

  canopy = read_tif(canopy)
  print(image)
  print(image.shape)
  
  packed_waypoints = gen_path(image, canopy, waypoints)
  print(packed_waypoints)
  x, y, z = packed_waypoints

  for smooth_param in smoothing_params:
    z = smooth_line(z, smooth_param) 

  points = []

  for x1, y1, z1 in zip(x,y,z):
    lon, lat = raster.affine * (x1, y1)
    points.append((lat, lon, z1))
  
  return points

import sys
if __name__ == '__main__':
  if len(sys.argv) < 4:
    print("not enough arguments")
    sys.exit() 
  
  bare_earth = sys.argv[1]
  canopy = sys.argv[2]
  path_file = sys.argv[3]
  
  print(path_file)
  path = [(x['latitude'], x['longitude']) for x in json.load(open(path_file))]
  
  new_path = plan_path(path, bare_earth, canopy)

  save_path('numpy_path.json', new_path,  None)
