import numpy

from src.constants import DEFAULT_WINDOW_SIZE


# A safe way of dividing numbers
def safe_division_transform(x, y, n_x, n_y, d_x, d_y):
    # Coordinates, Numerators, Denominators
    m_x = float(n_x) / d_x
    m_y = float(n_y) / d_y
    return int(m_x * x), int(m_y * y)


# This scales images into a dimension smaller than 512*512 for accessing values
def linear_transform(x, y, m_x, m_y):
    return safe_division_transform(
        x, y, m_x, m_y, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE)


# This scales images up to 512*512 for interaction
def inv_linear_transform(x, y, m_x, m_y):
    x_min, y_min = safe_division_transform(
        x, y, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE, m_x, m_y)
    x_max, y_max = safe_division_transform(
        x+1, y+1, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE, m_x, m_y)
    return numpy.arange(x_min, x_max), numpy.arange(y_min, y_max)


# This converts data pixels into 512*512 pixels, checks if already 512*512
def get_pixel_coords(points, rows, cols):
    if rows != DEFAULT_WINDOW_SIZE or cols != DEFAULT_WINDOW_SIZE:
        new_points = set()
        for x_coord, y_coord in points:
            x_arr, y_arr = inv_linear_transform(
                x_coord, y_coord, rows, cols)
            for x in x_arr:
                for y in y_arr:
                    new_points.add((x, y))
        return new_points
    return points


def get_first_entry(points):
    return next(iter(points))

