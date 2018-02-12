import arcpy as arc
import arcgisscripting as ag

from arcpy import env

env.workspace = 'C:/data'
data = '/Users/nnams/Documents/Workspace/Datasets/'
infile = data + 'USGS/'
folder_recursion = "RECURSION" # All files in the folder
process_entire_files = "PROCESS_ENTIRE_FILES"

las_dataset = arc.CreateUniqueName('tmp.lasd')
las_layer = 'tmp.layer'

print("Started LAS reclassification to none.")

arc.CheckOutExtension('3D')

arc.management.CreateLasDataset( input=infile
                               , out_las_dataset=las_dataset
                               , folder_recursion=folder_recursion
                               , relative_paths=False
                               )

arc.management.MakeLasDatasetLayer( las_dataset
                                  , las_layer
                                  )

arc.ddd.ChangeLasClassCodes( in_las_dataset=las_layer
                           , class_codes=[[i, 0] for i in range(1, 32)]
                           )

arc.management.Delete(las_layer)
arc.management.Delete(las_dataset)
arc.CheckInExtension('3D')

print( "Finished classifying points to none. Check if this is correct.")