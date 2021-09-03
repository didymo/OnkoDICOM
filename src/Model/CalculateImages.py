import numpy as np
from PySide6 import QtGui, QtCore

import src.constants as constant


def convert_raw_data(ds):
    """
    Convert the raw pixel data to readable pixel data in every image dataset

    :param ds: A dictionary of datasets of all the DICOM files of the patient
    :return: np_pixels, a list of pixel arrays of all slices of the patient
    """
    non_img_list = ['rtss', 'rtdose', 'rtplan', 'rtimage', 'sr-cd']
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
    :return: dict_img, a dictionary of scaled pixel arrays with the basic
    rescaling parameter
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


def scaled_pixmap(np_pixels, window, level, width, height):
    """
    Rescale the numpy pixels of image and convert to QPixmap for display.

    :param np_pixels: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :param width: Pixel width of the window
    :param height: Pixel height of the window
    :return: pixmap, a QPixmap of the slice
    """

    # Rescale pixel arrays
    np_pixels = np_pixels.astype(np.int16)
    if window != 0 and level != 0:
        # Transformation applied to each individual pixel to unique
        # contrast level
        np_pixels = (np_pixels - level) / window * 255
    else:
        max_val = np.amax(np_pixels)
        min_val = np.amin(np_pixels)
        np_pixels = (np_pixels - min_val) / (max_val - min_val) * 255

    np_pixels[np_pixels < 0] = 0
    np_pixels[np_pixels > 255] = 255
    np_pixels = np_pixels.astype(np.int8)

    # Convert numpy array data to QImage for PySide6
    bytes_per_line = np_pixels.shape[1]
    qimage = QtGui.QImage(
        np_pixels, np_pixels.shape[1], np_pixels.shape[0], bytes_per_line,
        QtGui.QImage.Format_Indexed8)

    pixmap = QtGui.QPixmap(qimage)
    pixmap = pixmap.scaled(width, height, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    return pixmap


def get_pixmaps(pixel_array, window, level, pixmap_aspect):
    """
    Get a dictionary of pixmaps.

    :param pixel_array: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :param pixmap_aspect: Scaling ratio for axial, coronal, and sagittal pixmaps
    :return: dict_pixmaps, a dictionary of all pixmaps within the patient.
    """
    # Convert pixel array to numpy 3d array
    pixel_array_3d = np.array(pixel_array)

    # Pixmaps dictionaries of 3 views
    dict_pixmaps_axial = {}
    dict_pixmaps_coronal = {}
    dict_pixmaps_sagittal = {}

    axial_width, axial_height = scaled_size(pixel_array_3d.shape[1]*pixmap_aspect["axial"], pixel_array_3d.shape[2])
    coronal_width, coronal_height = scaled_size(pixel_array_3d.shape[1],
                                                pixel_array_3d.shape[0] * pixmap_aspect["coronal"])
    sagittal_width, sagittal_height = scaled_size(pixel_array_3d.shape[2] * pixmap_aspect["sagittal"],
                                                  pixel_array_3d.shape[0])

    for i in range(pixel_array_3d.shape[0]):
        dict_pixmaps_axial[i] = scaled_pixmap(pixel_array_3d[i, :, :], window, level, axial_width, axial_height)

    for i in range(pixel_array_3d.shape[1]):
        dict_pixmaps_coronal[i] = scaled_pixmap(pixel_array_3d[:, i, :], window, level, coronal_width, coronal_height)
        dict_pixmaps_sagittal[i] = scaled_pixmap(pixel_array_3d[:, :, i], window, level, sagittal_width, sagittal_height)

    return dict_pixmaps_axial, dict_pixmaps_coronal, dict_pixmaps_sagittal


def scaled_size(width, height):
    if width > height:
        height = constant.DEFAULT_WINDOW_SIZE/width*height
        width = constant.DEFAULT_WINDOW_SIZE
    else:
        width = constant.DEFAULT_WINDOW_SIZE/height*width
        height = constant.DEFAULT_WINDOW_SIZE
    return width, height
