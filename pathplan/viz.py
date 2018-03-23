import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from pathplan.utils import distance, read_init_path
from pathplan.geo import wgs84
from scipy.interpolate import interp1d,griddata
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

def reduce_points(less, gt):
    tup_set = set([(x,y) for (x,y,z) in less])
 
    return [(x,y,z) for (x,y,z) in gt if (x,y) in tup_set]

def display_surface(path_one, path_two, ax):
    """
    Display a graph of the a surface between two paths. Expects the two
    input paths to have the same amount of data points. (ie len(one) == len(two))
    Args:
        path_one - List of waypoints in format [(x, y, z), (x, y, z), ...]
        path_two - List of waypoints in format [(x, y, z), (x, y, z), ...]
    """

    if len(path_one) > len(path_two):
        path_one = reduce_points(path_two, path_one)
    else:
        path_two = reduce_points(path_one, path_two)

    Z1 = 8.0
    Z2 = 9.0

    x1, y1, z1 = np.array(path_one).T
    x2, y2, z2 = np.array(path_two).T

    i, h = np.meshgrid(np.arange(len(x1)), np.linspace(Z1, Z2, 10))
    X = (x2[i] - x1[i]) / (Z2 - Z1) * (h - Z1) + x1[i]
    Y = (y2[i] - y1[i]) / (Z2 - Z1) * (h - Z1) + y1[i]
    Z = (z2[i] - z1[i]) / (Z2 - Z1) * (h - Z1) + z1[i]

    ax.set_xlabel("Distance along path (ft)")
    ax.set_ylabel("Distance along path (ft)")
    ax.set_zlabel("Altitude")
    #ax.plot(x1, y1, z1, 'k-', linewidth=1.4, color='b', label="Planned Path")
    #ax.plot(x2, y2, z2, 'k-', linewidth=1.4, color='r', label="Flown Path")
    ax.plot_surface(X, Y, Z, color='g', alpha=0.4, linewidth=0, label="Highlighted Error")

    # Proxy for displaying legend, as legends are not supported in 3d Plots:
    colors = ["blue", "red", "green"]
    proxy1 = matplotlib.lines.Line2D([0],[0], c=colors[0])
    proxy2 = matplotlib.lines.Line2D([0],[0], c=colors[1])
    proxy3 = matplotlib.lines.Line2D([0],[0], c=colors[2])
    #ax.legend([proxy1, proxy2, proxy3], ['Path1', 'Path2', 'Highlighted Error'], numpoints = 1)

def plot_lidar_penetration(path, dist, **kwargs):
  if 'ax' not in kwargs:
      fig = plt.figure()
      if 'dimen' not in kwargs:
          ax = fig.add_subplot(111)
      else:
          ax = fig.add_subplot(111, projection=kwargs['dimen'])
  else:
      ax = kwargs['ax']

  xs, ys = build_distance_lists(path)

  y_interp = interp1d(xs, ys)

  new_xs = np.arange(xs[0], xs[-1], abs(xs[0]-xs[-1]) / 1000)
  fake_ys = [y_interp(x) for x in new_xs]

  ys2 = []

  for y in fake_ys:
    ys2.append(y - dist)

  ax.fill_between(new_xs, fake_ys, ys2)
    

#Lines: tuple ((x1, y1), (x2, y2)) mapped to a list of LineStrings
# Each path is a tuple mapped to a list of LineStrings
# Plots distance along the path vs Z
def plot2d(lines, *paths, **kwargs): 
  
  surf_name, lines = lines
  if 'ax' not in kwargs:
      fig = plt.figure()
      ax = fig.add_subplot(111)
  else:
      ax = kwargs['ax']
  
  if len(lines) > 0:
      lines_graph_x = [0]
      lines_graph_y = [lines[0][2]]


      lines_graph_x, lines_graph_y = build_distance_lists(lines)

      if 'surf_color' not in kwargs:
          ax.plot(lines_graph_x, lines_graph_y, label=surf_name, color=kwargs['surf_color'])
      else:
          ax.plot(lines_graph_x, lines_graph_y, label=surf_name, color='r')
      
  #ax.scatter(lines_graph_x, lines_graph_y, label=surf_name, color='g')
  
  if 'colors' not in kwargs:
      colors = ['g'] * len(paths)
  else:
      colors = kwargs['colors']

  for ((name,path), col) in zip(paths, colors):
      print("plotting path {0}".format(name))
      path_x, path_y = build_distance_lists(path)

      ax.plot(path_x, path_y, label=name, color=col)


  ax.legend()

      #if 'scatter' not in kwargs: #and kwargs['scatter']:
      #    ax.scatter(path_x, path_y, color='g')
   
  
  
  ax.set_xlabel("Distance Along Path (feet)")
  ax.set_ylabel("Altitude (feet)")
  #plt.legend(loc='bottom left')
  #plt.show()

import rasterio
def plot3d(image, raster, proj, *paths, **kwargs):

  if 'ax' not in kwargs:
      fig = plt.figure()
      ax = fig.add_subplot(111, projection='3d')
  else:
      ax = kwargs['ax']

  print(paths)


  if 'colors' in kwargs:
    colors = kwargs['colors']
  else:
    colors = ['b'] * len(paths)

  for (name,waypoints),color in zip(paths,colors):
      print(waypoints)
      x_points, y_points, z_points = zip(*waypoints)
      ax.plot(x_points, y_points, zs=z_points, label=name, color=color)

  max_x = max(x_points)
  max_y = max(y_points)

  if 'plot_surface' in kwargs and not kwargs['plot_surface']:
    init_proj = pyproj.Proj(raster.crs, preserve_units=True)
    bounds = raster.bounds

    left, top = pyproj.transform(init_proj, proj, bounds.left, bounds.top)
    right, bottom = pyproj.transform(init_proj, proj, bounds.right, bounds.bottom)

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
    ax.plot_surface(x_raster[:, 1:], y_raster[:, 1:], image, cmap=cm.coolwarm,linewidth=0, antialiased=False)

    plt.show()
