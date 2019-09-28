import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from src.Model.LoadPatients import *
from src.Model.ROI import *


def convert_raw_data(ds):
    non_img_list = ['rtss', 'rtdoes', 'rtplan']
    np_pixels = []
    for key in ds:
        if key not in non_img_list:
            np_tmp = ds[key]
            np_tmp.convert_pixel_data()
            np_pixels.append(np_tmp._pixel_array)
    return np_pixels

def get_img(pixel_array):
    dict_img = {}
    for i, np_pixels in enumerate(pixel_array):
            max_val = np.amax(np_pixels)
            min_val = np.amin(np_pixels)
            np_pixels = (np_pixels - min_val) / (max_val - min_val) * 256
            np_pixels[np_pixels < 0] = 0
            np_pixels[np_pixels > 255] = 255
            np_pixels = np_pixels.astype("int8")
            dict_img[i] = np_pixels
    return dict_img

def scaled_pixmap(np_pixels, window, level):

    np_pixels = np_pixels.astype(np.int16)

    if window != 0 and level != 0:
        np_pixels = (np_pixels - level) / window * 255
    else:
        max_val = np.amax(np_pixels)
        min_val = np.amin(np_pixels)
        np_pixels = (np_pixels - min_val) / (max_val - min_val) * 255

    np_pixels[np_pixels < 0] = 0
    np_pixels[np_pixels > 255] = 255
    np_pixels = np_pixels.astype(np.int8)

    # Convert numpy array data to qimage for pyqt5
    qimage = QtGui.QImage(
        np_pixels, np_pixels.shape[1], np_pixels.shape[0], QtGui.QImage.Format_Indexed8)
    pixmap = QtGui.QPixmap(qimage)
    pixmap = pixmap.scaled(512, 512, QtCore.Qt.KeepAspectRatio)
    return pixmap


# Return a dictionary of pixmaps for UI
def get_pixmaps(pixel_array, window, level):

    # Create a dictionary of storing pixmaps
    dict_pixmaps = {}
    # List of non-image keys
    for i, np_pixels in enumerate(pixel_array):
        pixmap = scaled_pixmap(np_pixels, window, level)
        dict_pixmaps[i] = pixmap
    return dict_pixmaps