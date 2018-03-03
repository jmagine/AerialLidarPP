from path_planner import get_shapes_from_vector, get_vector_from_raster 
from shapely.geometry import MultiPolygon
from shapely.wkb import dumps
from os.path import basename, splitext

from argparse import ArgumentParser

parser = ArgumentParser(description="Generate Shapes and Altitudes from a geotiff")
parser.add_argument("geotif", type=str, help="geotif file to load data from")
parser.add_argument("output", type=str, help="directory to output the shapes into")

args = parser.parse_args()

print("making shapes")

vectors = get_vector_from_raster(args.geotif)
shapes, alt_dict = get_shapes_from_vector(vectors)

base = splitext(basename(args.geotif))[0]

binary = dumps(MultiPolygon(shapes))
with open(args.output+"/" + base + ".shapes", "wb") as wkb_file:
    wkb_file.write(binary)

import json
with open(args.output+"/"+base+".alt.json", "w") as alt_dict_file:
    json.dump(alt_dict, alt_dict_file)
