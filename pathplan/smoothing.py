from scipy.interpolate import splrep, splev
from pathplan.viz import build_distance_lists
from scipy.optimize import minimize_scalar 
from scipy.signal import argrelextrema

import numpy as np



def get_spline_derivative(t,c,k):
    dt = t[k+1:-1] - t[1:-k-1]

    d = (c[1:-1-k] - c[:-2-k]) * k / dt
   
    t2 = t[1:-1]

    d = np.r_[d, [0]*k]

    return t2, d, k-1
    
def concavity_smooth(path):
    xs, ys = build_distance_lists(path)

    spline = splrep(xs, ys)
    deriv = get_spline_derivative(*spline) 
 
    spline_func = lambda x: splev(x, spline)
    neg_spline_func = lambda x: -splev(x, spline)
    print(ys)
    mins,= argrelextrema(np.array(ys), np.less)
    maxs, = argrelextrema(np.array(ys), np.greater)

    print(mins)
    print(maxs)
    minima = np.sort(np.concatenate(mins, maxs), 0)

    deriv_func = lambda x: splev(x, deriv)
    deriv_xs = np.array([deriv_func(x) for x in xs])
    inflect1, = argrelextrema(deriv_xs, np.less)
    inflect2,= argrelextrema(deriv_xs, np.greater)

    inflect = np.sort(np.concatenate(inflect1, inflect2))

    points = []
    if inflect[0] < minima[0]:
        start = 0
        min_start = 1
    else:
        miny = spline_func(minima[0])
        inflecty = spline_func(inflect[0])
        points.append(minima[0], miny)
        if miny <= inflecty:
            points.append(inflect[0], inflecty)
        else:
            points.append(inflect[0], miny)
            points.append(inflect[0], inflecty)
        start = 0
        min_start = 1

    while start < len(inflect)-1:
        miny = spline_func(minima[min_start])
        inflecty = spline_func(inflect[start])
        inflecty2 = spline_func(inflect[start+1])
        if miny <= inflecty:
            points.append(minima[min_start], miny)
            points.append(inflect[start+1], inflecty2)
        else:
            points.append(inflect[start], miny)
            points.append(minima[min_start], miny)
            points.append(inflect[start+1], miny)
            points.append(inflect[start+1], inflecty2)
        start += 1
        min_start += 1

    dx = (points[0][0] - points[-1][0])
    dy = (points[0][1] - points[-1][1])

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

        

    

    
