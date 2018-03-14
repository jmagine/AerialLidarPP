from scipy.interpolate import bisplrep, bisplev


def spline_smoothing(path, segments, inter_point_distance):
    x, y, z = zip(*path)
    curve = bisplrep(x, y, z)
    new_path = []
    for (start,end) in segments:
        dx = end[0]-start[0]
        dy = end[1] - start[1]
        dist = ((dy)**2 + (dx)**2)**.5
        dx = (dx / dist) * inter_point_distance
        dy = (dy / dist) * inter_point_distance

        x = start[0]
        y = start[1]
 
        while x < end[0] and y < end[1]:
            new_path.append((x, y, bisplev(x,y,curve)))
            x += dx
            y += dy
 
    return new_path

