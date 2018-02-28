#WELCOME TO THE MASTER VIZ/EVALUATION SCRIPT
import subprocess
from shapely.strtree import STRtree
import json
from pathplan.path_planner_numpy import read_tif
from shapely.geometry import MultiPolygon
from shapely.wkb import dumps
from os.path import basename, splitext

from pathplan.path_planner import get_vector_from_raster,plan_path, get_shapes_from_vector, read_init_path
import pathplan.sitl as sitl
from pathplan.utils import load_shapefile, load_altfile


#returns path json, alt file, shapefile, and tif
def load_test_case(case_name):
    test_dict = json.load(open("tests/"+case_name))
    path, pro = read_init_path(test_dict['path'])
    tif = read_tif(test_dict['tif'])
    if "shapes" not in test_dict:
        test_dict['shapes'] = "gen/shapes/{0}.shapes".format(case_name)
        test_dict['alts'] = "gen/shapes/{0}.alt.json".format(case_name)
        save_test_case(case_name,test_dict)
        vecs = get_vector_from_raster(test_dict['tif'])
        shapes, alt = get_shapes_from_vector(vecs, test_dict['proj'])
        binary = dumps(MultiPolygon(shapes))
        with open(test_dict['shapes'], "wb") as wkb_file:
            wkb_file.write(binary)
         	
        with open(test_dict['alts'], "w") as alt_dict_file:
            json.dump(alt, alt_dict_file)
    else:
        shapes = load_shapefile(test_dict['shapes'])
        alt = load_altfile(test_dict['alts'])
    return path, alt, shapes, tif, test_dict

def generate_path(case_name, path_name, params):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    tree = STRtree(shapes)

    gen_path, lines = plan_path(path, tree, alt, params['be_buffer'],params['obs_buffer'], params['min_alt_change'], params['climb_rate'], params['descent_rate'], params['max_speed']) 
    test_dict['results'][path_name] = {'path':gen_path,'params': params}
    test_dict['results']['lines'] = lines
    save_test_case(case_name,test_dict)

def save_test_case(case_name, test_dict):
    json.dump(test_dict, open("tests/"+case_name, "w"))


import os

def generate_flight(case_name, path_name, port, logdir):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    if name not in test_dict['results']:
        print("Could not find the named path")
        return
    gen_path = test_dict['results'][path_name]['path']
    subprocess.call(["make", "killsitl"])
    subprocess.call(["make", "runsitl"])
    flown_path = sitl.fly(gen_path, port, os.getcwd() + "logs")
    test_dict['results'][path_name]['flight_path'] = flown_path
    save_test_case(case_name,test_dict)
    
    

#takes 
from pathplan.plots import plot2d, plot3d

def plot_3d_one(case_name, path_name):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    path = (path_name, test_dict['results'][path_name]['path'])
    plot3d(tif, True, path)

def plot_3d_all(case_name ):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    paths = []

    for (name,res) in test_dict['results']:
        paths.append((name, [res['path']])) 

    plot3d(tif, *paths)

def plot_2d_one(case_name, path_name):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    path = (path_name, test_dict['results'][path_name]['path'])
    lines = test_dict['results']['lines']
    plot2d(('surface',lines), path)

def plot_2d_all(case_name):
    path, alt, shapes, tif, test_dict = load_test_case(case_name)
    
    paths = []

    for (name,res) in test_dict['results']:
        paths.append((name, [res['path']])) 

    lines = test_dict['results']['lines']

    plot2d(lines, *paths)
    

def create_test_case(case_name, tif_path, path_path, proj):
    case_dict = {"tif": tif_path, "path": path_path, "proj":proj, "results":{}}
    save_test_case(case_name, case_dict)
    

def print_commands():
    print("create NAME TIF PATH PROJ      -- Creates a test case with the specified name, tif, path, and projection status")
    print("gen NAME PATH-NAME [PARAM]     -- Generates a path for the test case with optional param file specification")
    print("fly NAME PATH-NAME PORT        -- Runs the SITL to generate a flight path for the given path (Note: may take a while")
    print("plot-one-2d NAME PATH-NAME     -- Generates a 2d plot with one generated path")
    print("plot-all-2d NAME               -- Generates a 2d plot with all of the generated paths")
    print("plot-one-3d NAME PATH-NAME     -- Generates a 3d plot with one generated path")
    print("plot-all-3d NAME               -- Generates a 3d plot with all of the generated paths")
    print("set-params                     -- Interactively set the paramters for the algorithm")
    print("help                           -- Display this msg again")


if __name__ == '__main__':
    print("Welcome to the interactive testing/evaluation setup for the Aerial Lidar project")
    print("TODO: Add commands to generate tifs")
    print_commands()
 
    params = {}

    try:
        while True:
            command = raw_input("Enter Command: ").split(" ")
            if command[0] == 'create':
                if len(command) == 5:
                    create_test_case(*command[1:])
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'gen':
                if len(command) == 3 or len(command) == 4:
                    generate_path(*(command[1:] + [params]))
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'fly':
                if len(command) == 4:
                    generate_flight(*(command[1:] + ["logs"]))
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'plot-one-2d':
                if len(command) == 3:
                    plot_2d_one(*command[1:])
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'plot-all-2d':
                if len(command) == 2:
                    plot_2d_all(*command[1])
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'plot-one-3d':
                if len(command) == 3:
                    plot_3d_one(*command[1:])
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'plot-all-3d':
                if len(command) == 2:
                    plot_3d_all(*command[1])
                else:
                    print("Error incorrect # of args")
                    print_commands()
                continue
            elif command[0] == 'set-params':
                params['be_buffer'] = float(raw_input("Enter distance from bare earth: "))
                params['obs_buffer'] = float(raw_input("Enter distance from surfaces: ")) 
                params['min_alt_change'] = float(raw_input("Enter min alt change: "))
                params['climb_rate'] = float(raw_input("Enter climb_rate: ")) 
                params['descent_rate'] = float(raw_input("Enter descent rate: "))
                params['max_speed'] = float(raw_input("Enter maximum horizontal speed: "))
            elif command[0] == 'help':
                print_commands()
    except KeyboardInterrupt:
        print("Closing the Aerial Lidar interactive prompt") 

