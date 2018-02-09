#TODO Add pyproj to convert to meter grid
from rasterio.features import shapes
import rasterio
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, LineString, Polygon, MultiPolygon

import json
import math

import time

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

    return list(results)


def get_shapes_from_vector(vectors):
    alt_dict = {}
    shapes = []

    first_tup = vectors[0]['geometry']['coordinates'][0][0]

    print(first_tup)


    proj = utm_proj(first_tup[1], first_tup[0])

    def transform_to_proj(x, y, z=None):
        return pyproj.transform(wgs84, proj, x, y, z)

    init_time = time.time()
    for vec in vectors:
        shap = transform(transform_to_proj, shape(vec['geometry']))
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

    print("transforming the vectors took {0} seconds".format(time.time() - init_time))

    return shapes, alt_dict, proj



def distance(p1, p2):
    return sum(map(lambda s: (s[0] - s[1])**2, zip(p1, p2)))**.5


# Args:
#   path: (latitude, longitude) tuples
#   strtree: STRtree containing the topology of the area to explore
#   alt_dict: dict mapping shapely wkt to altitude
#   buffer: number representing how close we need to be to intersect
def plan_path(path, strtree, alt_dict, buffer):
    segments = []
    for i in range(1, len(path)):
        segments.append((path[i-1], path[i]))

    print("Built Segments")
    print("segments", segments)

    new_path  = []
    new_path.append((path[0][0], path[0][1], 0))

    for seg in segments:
        seg_points = []
        init_time = time.time()
        print("Started Segment")
        ls = LineString(seg).buffer(buffer)
        intersecting = list(strtree.intersection(ls))

        print("R Tree query returns {0} intersections".format(len(intersecting)))
        for inter in intersecting:

            for coord in g_coll:
                alt = alt_dict[g_coll.wkt]
                seg_points.append((coord[0], coord[1], alt + buffer))

        seg_points = list(sorted(seg_points, key=lambda x: distance(p1, x.coords[0])))

        new_path += seg_points

        print("Finished Segment in {0}".format(time.time() - init_time))
    return new_path

def read_init_path(filepath, proj):
    miss_dict = json.load(open(filepath))

    tups = []
    for wp in miss_dict:
        x, y, z = pyproj.transform(wgs84, proj, wp['longitude'], wp['latitude'],0)
        tups.append((x, y, z))

    return tups

#Also does projection
def save_path(filepath, path, proj):
    arr = []
    for x, y, z in path:
        lon, lat, alt = pyproj.transform(proj, wgs84, x, y, z)
        new_dict = {'latitude' : lat, 'longitude' : lon, 'altitude' : alt}
        arr.append(new_dict)

    json.dump(arr, open(filepath, 'w'))





if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("required arguments: geotiff file + path file + buffer")
        sys.exit()



    vectors = get_vector_from_raster(sys.argv[1])

    shapes, alt_dict, proj = get_shapes_from_vector(vectors)

    miss_waypoints = read_init_path(sys.argv[2], proj)

    tree = MultiPolygon(shapes)

    new_path = plan_path(miss_waypoints, tree, alt_dict, float(sys.argv[3]))

    save_path('path.json', new_path, proj)
