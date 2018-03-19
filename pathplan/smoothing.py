from scipy.interpolate import splrep, splev
from pathplan.viz import build_distance_lists
from scipy.optimize import minimize_scalar 
from scipy.signal import argrelextrema

import numpy as np



def concavity_smooth(path):
    xs, ys = build_distance_lists(path)

    spline = splrep(xs, ys)

    dists = np.linspace(xs[0], xs[-1])

    deriv = splev(spline, dists, der=1)
    second_deriv = splev(spline, dists, der=2)

    minima = list(sorted([dists[i] for x,i in enumerate(deriv) if x == 0]))
    inflect = list(sorted([dists[i] for x,i in enumerate(second_deriv) if x == 0 and x not in minima]))
    
    inflect_idx = 0
    minima_idx = 0
  
    points = []
    while inflect_idx < len(inflect) and minima_idx < len(minima):
        if minima[minima_idx] < inflect[inflect_idx]:
            pass
        else:
            pass
    
    dx = (path[0][0] - path[-1][0])
    dy = (path[0][1] - path[-1][1])

    norm = (dx**2 + dy**2)**.5

    unit_dx = dx / norm
    unit_dy = dy / norm

    new_points = []
    for point in points:
        x = start[0] + unit_dx * point[0]
        y = start[1] + unit_dx * point[0]
        z = point[1]
        new_points.append(x,y,z)
         
    return new_points

        

    

    
