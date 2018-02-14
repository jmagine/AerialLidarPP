import json
from shapely.wkb import loads


def load_shapefile(filename):
    with open("gen/"+filename+".shapes", "rb") as wkb_file:
        shapes = list(loads(wkb_file.read()))
    return shapes

def load_altfile(filename):
    with open("gen/"+filename+".alt.json") as alt_dict_file:
        alt_dict = json.load(alt_dict_file)
    return alt_dict
