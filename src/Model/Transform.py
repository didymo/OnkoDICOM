import numpy

from src.constants import DEFAULT_WINDOW_SIZE


def safe_division_transform(x, y, n_x, n_y, d_x, d_y):
    """
    This method is a robust way of transforming coordinates from size
    to another
    :param x: x coordinate
    :param y: y coordinate
    :param n_x: new row size
    :param n_y: new colum size
    :param d_x: old row size
    :param d_y: old column size
    :return: new scaled x,y coordinates
    """
    m_x = float(n_x) / d_x
    m_y = float(n_y) / d_y
    return int(m_x * x), int(m_y * y)


def linear_transform(x, y, m_x, m_y):
    """
    This function scales a point down from 512*512 to the required
    frame of reference
    :param x: x coordinate
    :param y: y coordinate
    :param m_x: new row size
    :param m_y: new column size
    :return: scaled down x,y coordinates
    """
    return safe_division_transform(
        x, y, m_x, m_y, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE)


def inv_linear_transform(x, y, m_x, m_y):
    """
    This function generates all points in a 512*512 image that map to x,y
    :param x: x coordinate
    :param y: y coordinate
    :param m_x: old row size
    :param m_y: old column size
    :return: two arrays with all possible x,y coordinates that scale down to
    the original x,y coordinates
    """
    x_min, y_min = safe_division_transform(
        x, y, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE, m_x, m_y)
    x_max, y_max = safe_division_transform(
        x+1, y+1, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_SIZE, m_x, m_y)
    return numpy.arange(x_min, x_max), numpy.arange(y_min, y_max)


# This converts data pixels into 512*512 pixels, checks if already 512*512
def get_pixel_coords(points, rows, cols):
    """
    Thi function transforms a set of coordinate points into their 512x512
    counterparts
    :param points: a set of coordiate points: (x,y)
    :param rows: old row size
    :param cols: old column size
    :return: a set of coordinates in a 512*512 frame of reference
    """
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
    """
    This function gets the first point from a set of points
    :param points: a set of points
    :return: the first entry of points
    """
    return next(iter(points))
