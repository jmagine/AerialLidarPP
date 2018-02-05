#TODO Add pyproj to convert to meter grid
from rasterio.features import shapes
from shapely.geometry import shape, LineString
from shapely.strtree import STRtree

import geopandas as gp
import rasterio

import sys


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

# Return 
def get_shapes_from_vector(vectors):
    alt_dict = {}
    shapes = []


    i = 10
    for vec in vectors:

        shap = shape(vec['geometry'])
        alt_dict[shap.wkt] = vec['properties']['raster_val']
        shapes.append(shap)

        if i == 0:
            break

        i -= 1

    return shapes, alt_dict

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

    return new_alt

def read_init_path(filepath):
    pass



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("required arguments: geotiff file + path file")
        sys.exit()


