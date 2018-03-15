'''
This file contains all methods for converting between different geoographical
projections and dealing with tif, shape, and altitude json files
'''


from rasterio.features import shapes
import rasterio
from shapely.ops import transform
from shapely.geometry import shape, LineString, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.wkb import dumps, loads
from affine import Affine
from PIL import Image
import pyproj
import numpy as np
import json
import time

import math

wgs84 = pyproj.Proj(init="epsg:4326")

def get_image_coord(raster, x, y):
  box = raster.bounds()
  width = box.right - box.left
  height = box.top -box.bottom
  x_perc = x / width
  y_perc = y / height
  
  return x_perc * raster.width, y_perc * raster.height

def utm_zone(lat, lon):
    """Determine the UTM zone for a given latitude and longitude.

    Based on http://gis.stackexchange.com/a/13292

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        zone number: UTM zone number lat/lon falls in
        north: bool indicating North/South
    """
    zone = math.floor((lon + 180) / 6.0) + 1

    # Special cases for Norway and Svalbard
    if lat >= 56 and lat < 64 and lon >= 3 and lon < 12:
        zone = 32

    if lat >= 72 and lat < 84:
        if lon >= 0 and lon < 9:
            zone = 31
        elif lon >= 9 and lon < 21:
            zone = 33
        elif lon >= 21 and lon < 33:
            zone = 35
        elif lon >= 33 and lon < 42:
            zone = 37

    return zone, lat > 0

def load_shapefile(filename):
    with open(filename, "rb") as wkb_file:
        shapes = list(loads(wkb_file.read()))
    return shapes

def load_altfile(filename):
    with open(filename) as alt_dict_file:
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


def proj_utm(zone, north):
    """Proj instance for the given zone.

    Args:
        zone: UTM zone
        north: North zone or south zone

    Returns:
        pyproj.Proj instance for the given zone
    """
    ref = "+proj=utm +zone=%d +ellps=WGS84" % zone
    if not north:
        ref += " +south"
    return pyproj.Proj(ref)


def utm_proj(lat, lon):
    """
    Returns the utm_proj for the given lat and lon
    """

    zone, north = utm_zone(lat, lon)
    return proj_utm(zone, north)


'''
Converts a raster file into a vector representation
e.g. goes from the pixelized raster to a series of shapes
mapped to altitude
'''
def vectorize_raster(rasterfile):

    results = None

    with rasterio.drivers():
        with rasterio.open(rasterfile) as src:
            image = src.read(1) # first band
            results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=None, transform=src.affine)))

    return list(results)


def shapelify_vector(vectors, do_transform=True):
    alt_dict = {}
    shapes = []

    #lol at the way that works
    lon, lat = vectors[0]['geometry']['coordinates'][0][0]

    proj = utm_proj(lat, lon)

    def transform_to_proj(x, y, z=None):
        return pyproj.transform(wgs84, proj, x, y, z)

    init_time = time.time()
    for vec in vectors:
        shap = shape(vec['geometry'])
        if do_transform:
            shap = transform(transform_to_proj, shap)
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

    print("transforming the vectors took {0} seconds".format(time.time() - init_time))

    return shapes, alt_dict
