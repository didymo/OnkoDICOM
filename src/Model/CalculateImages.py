import numpy as np
from PyQt5 import QtGui, QtCore


def convert_raw_data(ds):
    """
    Convert the raw pixel data to readable pixel data in every image dataset

    :param ds: A dictionary of datasets of all the DICOM files of the patient
    :return: np_pixels, a list of pixel arrays of all slices of the patient
    """
    non_img_list = ['rtss', 'rtdose', 'rtplan', 'rtimage']
    np_pixels = []

    # Do the conversion to every slice (except RTSS, RTDOSE, RTPLAN)
    for key in ds:
        if key not in non_img_list:
            # dataset of current slice
            np_tmp = ds[key]
            np_tmp.convert_pixel_data()
            np_pixels.append(np_tmp._pixel_array)
    return np_pixels


def get_img(pixel_array):
    """
    Get a dictionary of image numpy array with only simple rescaling

    :param pixel_array: A list of converted pixel arrays
    :return: dict_img, a dictionary of scaled pixel arrays with the basic rescaling parameter
    """
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
    """
    Rescale the numpy pixels of image and convert to QPixmap for display.

    :param np_pixels: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :return: pixmap, a QPixmap of the slice
    """
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


def get_pixmaps(pixel_array, window, level):
    """
    Get a dictionary of pixmaps.

    :param pixel_array: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :return: dict_pixmaps, a dictionary of all pixmaps within the patient.
    """
    # Create a dictionary of storing pixmaps
    dict_pixmaps = {}
    # List of non-image keys
    for i, np_pixels in enumerate(pixel_array):
        pixmap = scaled_pixmap(np_pixels, window, level)
        dict_pixmaps[i] = pixmap
    return dict_pixmaps