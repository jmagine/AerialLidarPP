import json
from shapely.wkb import loads
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from PIL import Image

import numpy as np


def load_shapefile(filename):
    with open("gen/"+filename+".shapes", "rb") as wkb_file:
        shapes = list(loads(wkb_file.read()))
    return shapes

def load_altfile(filename):
    with open("gen/"+filename+".alt.json") as alt_dict_file:
        alt_dict = json.load(alt_dict_file)
    return alt_dict

def read_tif(filename):
  #image = Image.open(filename)
  #image = np.array(image)
  #image = plt.imread(filename)
  #i_w = image.shape[0]
  #i_h = image.shape[1]
  #image = image.flatten().reshape((i_w, i_h))
  image = Image.open(filename).convert('L')
  image = np.array(image)
  return image

def plot_path(image, x_points, y_points, z_points):
  x_raster = np.arange(0, image.shape[0], step=1)
  y_raster = np.arange(0, image.shape[1], step=1)
  x_raster, y_raster = np.meshgrid(x_raster, y_raster)

  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')
  ax.plot(x_points, y_points, zs=z_points)
  ax.plot_surface(y_raster, x_raster, image, cmap=cm.coolwarm,linewidth=0, antialiased=False)
  plt.show()
