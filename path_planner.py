#TODO Add pyproj to convert to meter grid
from rasterio.features import shapes
from shapely.geometry import shape, LineString, Polygon
from shapely.strtree import STRtree
import pyproj

import geopandas as gp
import rasterio
import json
import math

import sys

wgs84 = pyproj.Proj(init="epsg:4326")

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


def get_vector_from_raster(rasterfile):

    results = None

    with rasterio.drivers():
        with rasterio.open(rasterfile) as src:
            image = src.read(1) # first band
            results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=None, transform=src.affine)))

    return results

def get_shapes_from_vector(vectors):
    alt_dict = {}
    shapes = []

    proj = utm_proj(vectors[0].coords[0][0], vectors[0].coords[0][1])

    for vec in vectors:
        shap = shape(vec['geometry'])
        shap = Polygon(list(map(lambda x: pyproj.transform(wgs84, proj, x[0], x[1], 0), shap.coords)))
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

    return shapes, alt_dict, proj



def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)**.5


# Args:
#   path: (latitude, longitude) tuples
#   strtree: STRtree containing the topology of the area to explore
#   alt_dict: dict mapping shapely wkt to altitude
#   buffer: number representing how close we need to be to intersect
def plan_path(path, strtree, alt_dict, buffer):
    segments = []
    for i in range(1, len(path)):
        segments.append((path[i-1], path[i]))

    new_path  = []
    new_path.append((path[0][0], path[0][1], 0))

    for seg in segments:
        ls = LineString(seg)
        intersecting = list(strtree.query(ls.buffer(buffer)))

        for inter in intersecting:
            g_coll = ls.intersection(inter)
            g_coll = list(sorted(g_coll, lambda x: distance(p1, x.coords[0])))

            for int_line in g_coll:
                alt = alt_dict[int_line.wkt]
                coord = int_line.coords[0]
                new_path.append((coord[0], coord[1], alt + buffer))

    return new_path

def read_init_path(filepath):
    miss_dict = json.load(open(filepath))

    tups = []
    for wp in miss_dict:
        tups.append((miss_dict['latitude'], miss_dict['longitude'], miss_dict['altitude']))

    return tups

#Also does projection
def save_path(filepath, path, proj):
    arr = []
    for x, y, z in path:
        lon, lat, alt = pyproj.transform(proj, wgs84, x, y, z)
        new_dict = {'latitude' : latitude, 'longitude' : lon, 'altitude' : z}
        arr.append(new_dict)

    json.dump(arr, open(filepath))





if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("required arguments: geotiff file + path file + buffer")
        sys.exit()


    miss_waypoints = read_init_path(sys.argv[2])

    vectors = get_vector_from_raster(sys.argv[1])

    shapes, alt_dict, proj = get_shapes_from_vector(vectors)

    new_path = plan_path(miss_waypoints, shapes, alt_dict, float(sys.argv[3]))

    save_path('path.json', new_path, proj)
