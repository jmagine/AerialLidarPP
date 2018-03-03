import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from path_planner import distance, read_init_path

#Lines: tuple ((x1, y1), (x2, y2)) mapped to a list of LineStrings
# Each path is a tuple mapped to a list of LineStrings
# Plots distance along the path vs Z
def plot2d(lines, *paths):
  surf_name, lines = lines
  accum_dist = 0 
  lines_graph_x = [0]
  lines_graph_y = [lines[0][2]]

  fig = plt.figure()
  ax = fig.add_subplot(111)

  for (idx,point) in enumerate(lines[1:]):
      last_point = lines[idx-1] 
      accum_dist += distance(last_point, point)
      lines_graph_x.append(accum_dist)
      lines_graph_y.append(point[2])
  
  ax.plot(lines_graph_x, lines_graph_y, label=surf_name, color='r')
  
  accum_dist = 0

  for (name,path) in paths:
      print("plotting a path")
      path_x = [0]
      path_y = [path[0][2] * .3048]
      for (idx,point) in enumerate(path[1:]):
          last_point = path[idx-1] 
          accum_dist += distance(last_point, point)
          path_x.append(accum_dist)
          path_y.append(point[2])

      print(len(path_x))
      ax.plot(path_x, path_y, label=name)
      ax.scatter(path_x, path_y, color='g')
      accum_dist = 0
   
  
  
  ax.set_xlabel("Distance Along Path (feet)")
  ax.set_ylabel("Altitude (feet)")
  plt.legend(loc='bottom left')
  plt.show()

def plot3d(image, small, *paths):
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  print(paths)

  for name,waypoints in paths:
      x_points, y_points, z_points, speed = zip(*waypoints)
      ax.plot(x_points, y_points, zs=z_points, label=name)

  #if small:
  #  max_x = max(x_points)
  #  max_y = max(y_points)
  #  print(max_x, max_y)
  #  print(image[0:max_y+1, 0:max_x+1].shape)

  #  x_raster = np.arange(0, max_x + 1, step=1)
  #  y_raster = np.arange(0, max_y + 1, step=1)
  #  x_raster, y_raster = np.meshgrid(x_raster, y_raster)
  #  ax.plot_surface(x_raster, y_raster, image[0:max_y+1, 0:max_x+1], cmap=cm.coolwarm,linewidth=0, antialiased=False)
  #else:
  #  x_raster = np.arange(0, image.shape[1], step=1)
  #  y_raster = np.arange(0, image.shape[0], step=1)
  #  x_raster, y_raster = np.meshgrid(x_raster, y_raster)
  #  ax.plot_surface(x_raster, y_raster, image, cmap=cm.coolwarm,linewidth=0, antialiased=False)

      
  plt.show()


