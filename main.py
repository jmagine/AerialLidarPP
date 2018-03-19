#WELCOME TO THE MASTER VIZ/EVALUATION SCRIPT
import subprocess
import traceback
from shapely.strtree import STRtree
import json
from shapely.geometry import MultiPolygon
from shapely.wkb import dumps
from os.path import basename, splitext

from pathplan.geo import vectorize_raster, shapelify_vector, read_tif, load_shapefile, load_altfile
from pathplan.path_planner import plan_path
from pathplan.utils import read_init_path, save_path
import pathplan.sitl as sitl
from pathplan.evaluation import calculate_intersections, mse, print_comparison_info


#returns path json, alt file, shapefile, and tif
def load_test_case(case_file):
    test_dict = json.load(open(case_file))
    path, pro = read_init_path(test_dict['path'])
    tif, tif_proj = read_tif(test_dict['tif'])
    if "shapes" not in test_dict:
        test_dict['shapes'] = "gen/shapes/{0}.shapes".format(splitext(case_file)[0])
        test_dict['alts'] = "gen/shapes/{0}.alt.json".format(splitext(case_file)[0])
        save_test_case(case_file,test_dict)

        vecs = vectorize_raster(test_dict['tif'])
        shapes, alt = shapelify_vector(vecs, test_dict['proj'])
        binary = dumps(MultiPolygon(shapes))

        with open(test_dict['shapes'], "wb") as wkb_file:
            wkb_file.write(binary)
         	
        with open(test_dict['alts'], "w") as alt_dict_file:
            json.dump(alt, alt_dict_file)
    else:
        shapes = load_shapefile(test_dict['shapes'])
        alt = load_altfile(test_dict['alts'])

    return path, alt, shapes, tif, pro, tif_proj, test_dict

def gen_path(path, alt, shapes, tif, proj, tif_proj, test_case, path_name, params_file, case_file):
    params = json.load(open(params_file))
    tree = STRtree(shapes)

    case_name = basename(splitext(case_file)[0])

    gen_path, lines = plan_path(path, tree, alt, params['be_buffer'],params['obs_buffer'], params['min_length'], params['climb_rate'], params['descent_rate'], params['max_speed'], params['min_speed']) 

    lines_file = 'tests/lines/{0}.json'.format(case_name)
    json.dump(lines, open(lines_file, 'w'))

    test_case['lines'] = lines_file

    path_loc = 'tests/gen-paths/{0}.json'.format(path_name)
    save_path(path_loc, gen_path,  proj)
    test_case['results'][path_name] = {}
    test_case['results'][path_name]['gen-path'] = path_loc
    test_case['results'][path_name]['params'] = params_file
    save_test_case(case_file,test_case)

    return gen_path

def generate_path(case_file, path_name, params_file): 
    path, alt, shapes, tif, pro, tif_proj, test_case = load_test_case(case_file)
    return gen_path(path, alt, shapes, tif, pro, tif_proj, test_case, path_name, params_file, case_file)

def save_test_case(case_name, test_dict):
    print(case_name, "case name")
    json.dump(test_dict, open(case_name, "w"))


import os

def generate_flight(case_name, path_name, port, logdir):
    path, alt, shapes, tif,proj, tif_proj, test_dict = load_test_case(case_name)
    print(path_name)
    if path_name not in test_dict['results']:
        print("Could not find the named path")
        return
    
    os.chdir(os.path.expanduser('~/CSE145/AerialLidarPP'))
    #subprocess.call(["make", "killsitl"])
    #subprocess.call(["make", "runsitl"])
    bin_path = sitl.fly(port, test_dict['results'][path_name]['gen-path'], "tests/flights/{0}".format(case_name))
    flown_path = sitl.parse_bins(bin_path)
    flight_loc = "tests/flights/{0}.json".format(case_name)
    json.dump(flown_path, open(flight_loc, "w")), 
    test_dict['results'][path_name]['flight_path'] = flight_loc
    save_test_case(case_name,test_dict)

    return flown_path
    
    

#takes 
from pathplan.viz import plot2d, plot3d

import rasterio
def plot_3d_one(case_name, *path_names):
    path, alt, shapes, tif,proj, test_dict = load_test_case(case_name)

    raster = rasterio.open('tests/'+test_dict['tif'])
    paths = []
  
    for path_name in path_names:
        path, _ = read_init_path(test_dict['results'][path_name]['gen-path'])
        paths.append((path_name, path))

    plot3d(tif,raster,proj, *paths)

def plot_2d_one(case_name, *plots):
    paths = []
    path, alt, shapes, tif,proj, test_dict = load_test_case(case_name)
    lines = json.load(open(test_dict['lines']))
    print(lines)
    for path_name in plots:
        print(path_name)
        path, _ = read_init_path(test_dict['results'][path_name]['gen-path'])
        path = (path_name, path)
        paths.append(path)
    plot2d(('surface',lines), False, *paths)


def create_test_case(case_name, tif_path, path_path, proj, param):
    case_dict = {"tif": tif_path, "path": path_path, "proj":proj, "param":param, "results":{}}
    save_test_case(case_name, case_dict)


def compare_to_flight(case_name, path_name):
    path, alt, shapes, tif,proj, test_dict = load_test_case(case_name)
    flight,_ = read_init_path(test_dict['results'][path_name]['flight_path'])
    
    perform_comparisons(test_dict, (flight, "flight"), path_name)

def compare_to_base(case_name, base, *paths):
    path, alt, shapes, tif,proj, test_dict = load_test_case(case_name)
    base_name = base
    base, _ = read_init_path(base)

    perform_comparisons(test_dict, (base, base_name), *paths)
    


def perform_comparisons(test_case, base, *paths):
    base, base_name = base
    for path_name in paths:
        path, _ = read_init_path(test_case['results'][path_name]['gen-path'])
        print_comparison_info(base, path, base_name, path_name)
    
    

def print_commands():
    print("create NAME TIF PATH PROJ PARAM              -- Creates a test case with the specified name, tif, path, and projection status")
    print("gen-np NAME                                  -- Generates a path for the test case with with the numpy alg")
    print("gen NAME PATH-NAME PARAMS                    -- Generates a path for the test case with the shapely algorithm")
    print("fly NAME PATH-NAME PORT                      -- Runs the SITL to generate a flight path for the given path (Note: may take a while")
    print("plot-2d CASE NAME [NAMES ...]                -- Generates a 2d plot with one generated path")
    print("plot-2d-all CASE                             -- Generates a 2d plot with all generated paths for the test case")
    print("plot-2d-with-flight CASE NAME [NAMES...]     -- Generates a 2d plot with all of the generated paths")
    print("plot-3d CASE NAME [NAMES ...]                -- Generates a 3d plot with one generated path")
    print("plot-3d-all CASE                             -- Generates a 3d plot with all of the generated paths")
    print("plot-3d-with-flight CASE NAME [NAMES...]     -- Generates a 2d plot with all of the generated paths")
    print("compare-to-paths CASE BASE PATH [PATHS]       -- Prints comparison information about the two paths")
    print("compare-to-flight CASE PATH                  -- Prints comparison information about the generated path and the flight path")
    print("new-params  NAME                             -- Interactively set the parameters for the algorithm")
    print("help                                         -- Display this msg again")


if __name__ == '__main__':
    print("Welcome to the interactive testing/evaluation setup for the Aerial Lidar project")
    print("TODO: Add commands to generate tifs")
    print_commands()
 
    params = {}

    try:
        while True:
            try:
                command = input("Enter Command: ").split(" ")
                if command[0] == 'create':
                    if len(command) == 6:
                        create_test_case(*command[1:])
                    else:
                        print("Error incorrect # of args")
                        print_commands()
                    continue
                elif command[0] == 'gen':
                    if len(command) == 4:
                        generate_path(*(command[1:]))
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
                elif command[0] == 'plot-2d':
                    if len(command) > 2:
                        plot_2d_one(*command[1:])
                    else:
                        print("Error incorrect # of args")
                        print_commands()
                    continue
                elif command[0] == 'plot-all-2d':
                    if len(command) == 2:
                        plot_2d_all(command[1])
                    else:
                        print("Error incorrect # of args")
                        print_commands()
                    continue
                elif command[0] == 'plot-3d':
                    if len(command) > 2:
                        plot_3d_one(*command[1:])
                    else:
                        print("Error incorrect # of args")
                        print_commands()
                    continue
                elif command[0] == 'plot-all-3d':
                    if len(command) == 2:
                        _,_,_,_,_,test_dict = load_test_case(command[1])
                        plot_3d_one(command[1], *test_dict['results'])
                    else:
                        print("Error incorrect # of args")
                        print_commands()
                    continue
                elif command[0] == 'compare-paths':
                    if len(command) > 4:
                        print("Error incorrect # of args") 
                        print_commands()
                    else:
                        compare_to_base(*command[1:])
                elif command[0] == 'compare-to-flight':
                    if len(command) == 4:
                        print("Error incorrect # of args") 
                        print_commands()
                    else:
                        compare_to_flight(*command[1:])
                elif command[0] == 'new-params':
                    if len(command) != 2:
                        print("Incorrect number of args")
                        print_commands()
                    else:
                        params = {}
                        params['be_buffer'] = float(input("Enter distance from bare earth: "))
                        params['obs_buffer'] = float(input("Enter distance from surfaces: ")) 
                        params['min_length'] = float(input("Enter min alt change: "))
                        params['climb_rate'] = float(input("Enter climb_rate: ")) 
                        params['descent_rate'] = float(input("Enter descent rate: "))
                        params['max_speed'] = float(input("Enter maximum horizontal speed: "))
                        json.dump(params, open('tests/params/{0}.json'.format(command[1]), 'w'))
                elif command[0] == 'help':
                    print_commands()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                print("There was a problem, please try again")
                traceback.print_exc()
    except KeyboardInterrupt:
        print("Closing the Aerial Lidar interactive prompt") 


