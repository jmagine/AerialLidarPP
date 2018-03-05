import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from path_planner import distance, read_init_path
from path_planner import distance
from geo import wgs84
import numpy as np
import pyproj

def build_distance_lists(tups):
    print(tups)
    xs = [0]
    last = tups[0]
    ys = [last[2]]
    acc_dist = 0

    for tup in tups[1:]:
        acc_dist += distance(last, tup)
        xs.append(acc_dist)
        ys.append(last[2])
        last = tup 

    return xs, ys

#Lines: tuple ((x1, y1), (x2, y2)) mapped to a list of LineStrings
# Each path is a tuple mapped to a list of LineStrings
# Plots distance along the path vs Z
def plot2d(lines, scatter=False, *paths): 
  surf_name, lines = lines
  accum_dist = 0 
  lines_graph_x = [0]
  lines_graph_y = [lines[0][2]]

  fig = plt.figure()
  ax = fig.add_subplot(111)

  lines_graph_x, lines_graph_y = build_distance_lists(lines)

  ax.plot(lines_graph_x, lines_graph_y, label=surf_name, color='r')
  
  for (name,path) in paths:
      print("plotting a path")
      path_x, path_y = build_distance_lists(path)

      ax.plot(path_x, path_y, label=name)

      if scatter:
          ax.scatter(path_x, path_y, color='g')
   
  
  
  ax.set_xlabel("Distance Along Path (feet)")
  ax.set_ylabel("Altitude (feet)")
  plt.legend(loc='bottom left')
  plt.show()

import rasterio
def plot3d(image, raster, proj, *paths):

  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  print(paths)

  for name,waypoints in paths:
      x_points, y_points, z_points = zip(*waypoints)
      ax.plot(x_points, y_points, zs=z_points, label=name)

  max_x = max(x_points)
  max_y = max(y_points)

  bounds = raster.bounds

  left, top = pyproj.transform(wgs84, proj, bounds.left, bounds.top)
  right, bottom = pyproj.transform(wgs84, proj, bounds.right, bounds.bottom)

  print(bounds)
  print(raster.width)
  print(raster.height)

  width = right - left 
  x_step = width / raster.width

  
  height = abs(top - bottom)
  y_step = height / raster.height

  print(x_step)
  print(y_step)

  x_raster = np.arange(int(left), int(right), step=x_step)
  y_raster = np.arange(int(bottom), int(top), step=y_step)

  print(len(x_raster))
  print(len(y_raster))

  x_raster, y_raster = np.meshgrid(x_raster, y_raster)

  print(len(x_raster))
  print(len(y_raster))
  print(image.shape)
  print(x_raster.shape)
  print(y_raster.shape)
  ax.plot_surface(x_raster[1:, 1:], y_raster[1:, 1:], image, cmap=cm.coolwarm,linewidth=0, antialiased=False)

  plt.show()
