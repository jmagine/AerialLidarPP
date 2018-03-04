import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from path_planner import distance, read_init_path
from path_planner import distance

def build_distance_lists(tups):
    xs = [0]
    last = tups[0]
    ys = last[0][2]
    acc_dist = 0

    for tup in tups[1:]:
        acc_dist += distance(last, tup)
        xs.append(acc_dist)
        ys.append(last[0][2])
        last = tup 

    return xs, ys

#Lines: tuple ((x1, y1), (x2, y2)) mapped to a list of LineStrings
# Each path is a tuple mapped to a list of LineStrings
# Plots distance along the path vs Z
def plot2d(lines, *paths, scatter=False):
  surf_name, lines = lines
  accum_dist = 0 
  lines_graph_x = [0]
  lines_graph_y = [lines[0][2]]

  fig = plt.figure()
  ax = fig.add_subplot(111)

  lines_graph_x, lines_graph_y = build_distance_list(lines)

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

def plot3d(image, *paths, small=True):

  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  print(paths)

  for name,waypoints in paths:
      x_points, y_points, z_points, speed = zip(*waypoints)
      ax.plot(x_points, y_points, zs=z_points, label=name)

  if small:
    max_x = max(x_points)
    max_y = max(y_points)
    print(max_x, max_y)
    print(image[0:max_y+1, 0:max_x+1].shape)

    x_raster = np.arange(0, max_x + 1, step=1)
    y_raster = np.arange(0, max_y + 1, step=1)
    x_raster, y_raster = np.meshgrid(x_raster, y_raster)
    ax.plot_surface(x_raster, y_raster, image[0:max_y+1, 0:max_x+1], cmap=cm.coolwarm,linewidth=0, antialiased=False)
  else:
    x_raster = np.arange(0, image.shape[1], step=1)
    y_raster = np.arange(0, image.shape[0], step=1)
    x_raster, y_raster = np.meshgrid(x_raster, y_raster)
    ax.plot_surface(x_raster, y_raster, image, cmap=cm.coolwarm,linewidth=0, antialiased=False)

  plt.show()
