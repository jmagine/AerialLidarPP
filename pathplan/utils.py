import json
import pyproj
from geo import utm_proj, wgs84

def read_init_path(filepath, proj=None):
    miss_dict = json.load(open(filepath))

    tups = []
    for wp in miss_dict:
	if proj == None:
	    proj = utm_proj(wp['latitude'], wp['longitude'])

	coord = pyproj.transform(wgs84, proj, wp['longitude'], wp['latitude'],0)
	if 'altitude' in wp:
	    coord = (coord[0], coord[1], wp['altitude'] * 3.28084)
	tups.append(coord)

    return tups, proj

#Also does projection
def save_path(filepath, path, proj):
    arr = []
    for lon, lat, alt, speed in path:
        if proj != None:
            lon, lat, alt = pyproj.transform(proj, wgs84, lon, lat, alt)
        new_dict = {'latitude' : lat, 'longitude' : lon, 'altitude' : alt * .3048, 'speed':speed}
        arr.append(new_dict)

    json.dump(arr, open(filepath, 'w'))
