from rasterio.features import shapes
from shapely.geometry import shape

import geopandas as gp

import rasterio


def get_shapes_from_raster(rasterfile):
    shapelies = None
    with rasterio.drivers():
        with rasterio.open(rasterfile) as src:
            image = src.read(1) # first band
            results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=mask, transform=src.affine)))

            shapelies = []
            for result in results:
                shapelies.append(shape(result['geometry']))

    return shapelies

def get_geoframe_from_raster(rasterfile):
    shapefiles = get_shapes_from_raster(rasterfile)
    df = gp.GeoDataFrame.from_features(shapefiles)
    return df
