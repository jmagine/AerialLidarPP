""" NOTE
Requires ArcGIS Desktop (ArcMap) to be installed. The installation window of
ArcGIS will install Python 2.7 for you. You'll need it to run this script.
All of the `arcpy` and `arcgisscripting` packages are directly referenced
from the python2.7 installation, so make sure to specifically use that python.
"""

import arcpy as arc
import arcgisscripting as ag

from arcpy import env

# Set the absolute path to where all the LAS datafiles are at.
data = '\\Users\\nnams\\Documents\\Workspace\\Datasets\\'

# I put all the LAS files in an extra subdirectory: USGS
infile = data + '/USGS'
folder_recursion = "RECURSION"

outfile = data + 'USGS.tif'

# Filter points that are only classified as:
class_codes = [2] # Ground

# Raster Parameters:
gentype = 'ELEVATION' # ELEVATION, INTENSITY, RGB

# interpolation = 'TRIANGULATION LINEAR WINDOW_SIZE 10'
interpolation = 'BINNING AVERAGE NATURAL_NEIGHBOR'

data_type = 'FLOAT'
sampling_type = 'CELLSIZE'
sampling_value = 10
z = 3.28

# Need to set a space where all our temporary files will be located at:
env.workspace = 'C:/data'

try:
    # Temporarily created dataset. Might be useful not to delete in the
    # future, but for now, after this, it gets cleaned up.
    las_dataset = 'tmp.lasd'

    arc.management.CreateLasDataset( input=infile
                                   , out_las_dataset=las_dataset
                                   , folder_recursion=folder_recursion
                                   , relative_paths=False
                                   )

    # Issues ran into: this file won't get generated in the env.worspace
    # directory when MakeLasDatasetLayer(.., CreateUniqueName('tmp.layer'))
    # is called so LasDatasetToRaster will in fact not be able to find it.
    # Hence, just call MakeLasDatasetLayer(.., 'tmp.layer') and have it be
    # located somewhere arbitrarily (We can check that it gets generated
    # properly by calling it again. This seems to be deleted after the program
    # ends anyways so don't have to worry too much about files appearing)
    #        las_layer = arc.CreateUniqueName('tmp.layer')
    las_layer = 'tmp.layer'
    arc.management.MakeLasDatasetLayer( las_dataset
                                      , las_layer
                                      , class_code=class_codes
                                      )

    # API Ref: http://resources.arcgis.com/en/help/main/10.1/index.html#//001200000052000000
    arc.conversion.LasDatasetToRaster( in_las_dataset=las_layer
                                     , out_raster=outfile
                                     , value_field=gentype
                                     , interpolation_type=interpolation
                                     , data_type=data_type
                                     , sampling_type=sampling_type
                                     , sampling_value=sampling_value
                                     , z_factor=z
                                     )
except arc.ExecuteError:
    print(arc.GetMessages())

except Exception as err:
    print(err.args[0])

finally:
    # Delete all of the intermediary files that we created along the
    # way that are saved to the env.workspace directory. Note: some
    # artifacts still remain after the conversion to rastere such as
    # xml.tif which will appears in the directory the tif is saved to.
    arc.management.Delete(las_layer)
    arc.management.Delete(las_dataset)