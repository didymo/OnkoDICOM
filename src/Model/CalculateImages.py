import cv2
import numpy as np
import pydicom
from PySide6 import QtCore, QtGui

import src.constants as constant


def convert_raw_data(ds, rescaled=True, is_ct=False):
    """
    Convert the raw pixel data to readable pixel data in every image dataset
    :param ds: A dictionary of datasets of all the DICOM files of the patient
    :param rescaled: A boolean to determine if the data has already
    been rescaled
    :param is_ct: Boolean to determine if data is CT for rescaling
    :return: np_pixels, a list of pixel arrays of all slices of the patient
    """
    non_img_list = ['rtss', 'rtdose', 'rtplan', 'rtimage']
    np_pixels = []

    # Invert pixel colour of MONOCHROME1-style images
    inverted = (ds[0].PhotometricInterpretation == "MONOCHROME1")

    # Do the conversion to every slice (except RTSS, RTDOSE, RTPLAN)
    for key in ds:
        if key not in non_img_list:
            if isinstance(key, str) and key[0:3] == 'sr-':
                continue
            else:
                # dataset of current slice
                np_tmp = ds[key]
                np_tmp.convert_pixel_data()
                if not rescaled:
                    # Perform the rescale
                    data_arr = np_tmp._pixel_array
                    slope, intercept = get_rescale(np_tmp, is_ct)
                    data_arr = (data_arr * slope + intercept)
                    # Store the rescaled data
                    ds[key]._pixel_array = data_arr
                np_pixels.append(np_tmp._pixel_array)

    # Invert the colours based on max value
    if inverted:
        max_val = np.amax(np_pixels)
        np_pixels_inverted = np.multiply(np_pixels, -1)
        np_pixels_inverted = np.add(np_pixels_inverted, max_val)
        return np_pixels_inverted

    return np_pixels


def get_rescale(np_tmp, is_ct):
    """
    For an image, grabs the rescale slope and rescale intercept
    :param np_tmp: an image
    :param is_ct: boolean to determine if axis rescale is necessary for
    CT images
    :return: the slope and y-intercept of the rescaling
    """
    slope = 1
    intercept = 0
    if 'RescaleSlope' in np_tmp:
        if isinstance(np_tmp.RescaleSlope, pydicom.valuerep.DSfloat):
            slope = np_tmp.RescaleSlope
        elif isinstance(np_tmp.RescaleSlope,
                        pydicom.multival.MultiValue):
            slope = np_tmp.RescaleSlope[1]

    if 'RescaleIntercept' in np_tmp:
        if isinstance(np_tmp.RescaleIntercept,
                      pydicom.valuerep.DSfloat):
            intercept = int(np_tmp.RescaleIntercept)
        elif isinstance(np_tmp.RescaleIntercept,
                        pydicom.multival.MultiValue):
            intercept = int(np_tmp.RescaleIntercept[1])

    if is_ct:
        intercept += constant.CT_RESCALE_INTERCEPT

    return slope, intercept


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


def scaled_pixmap(np_pixels, window, level, width, height,
                  fusion=False, color=None):
    """
    Rescale the numpy pixels of image and convert to QPixmap for display.

    :param np_pixels: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :param width: Pixel width of the window
    :param height: Pixel height of the window
    :param fusion: Boolean to set scaling for overlayed images
    :param color: String for conversion of pixels to specified color map
    :return: pixmap, a QPixmap of the slice
    """

    ''' The numpy pixel array is converted to a signed int before any additional operations are applied.
    This is due to the pydicom.dataset.Dataset.convert_pixel_data() function returning a numpy array of dtype uint16.
    The dtype is dependent on the DICOM elements: BitsAllocated and PixelRepresentation.
    dtype could theoretically return any combination of unsigned/signed 1, 8, 16, 32, or 64 bit values.
    Undefined behaviour when np_pixels is any type other than uint16 or int16. '''
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

    # Process heatmap for conversion of the np_pixels to rgb for the purpose
    # of displaying the PT/CT view in RGB colorspace.

    # Convert numpy array data to QImage for PySide6
    if color == "Heat":

        pixmap = QtGui.QPixmap(convert_pt_to_heatmap(np_pixels))

    else:
        # Generate a grayscale image and set pixmap to the image
        bytes_per_line = np_pixels.shape[1]

        qimage = QtGui.QImage(
            np_pixels,
            np_pixels.shape[1],
            np_pixels.shape[0],
            bytes_per_line,
            QtGui.QImage.Format_Indexed8)

        pixmap = QtGui.QPixmap(qimage)

    if fusion:
        width = constant.DEFAULT_WINDOW_SIZE
        height = constant.DEFAULT_WINDOW_SIZE

    # Rescale the image accordingly
    pixmap = pixmap.scaled(width, height, QtCore.Qt.IgnoreAspectRatio,
                           QtCore.Qt.SmoothTransformation)
    return pixmap


def convert_pt_to_heatmap(np_pixels):
    """
    Converts the grayscale of the pixel array associated with the PET images
    to a RGB image with a colormap/heat map applied to it.

    Returns:
        qimage [Qimage]: The converted heatmap
    """
    # Conversion of the array to UINT8, color spaces do not like int8.
    arr8 = np_pixels.astype(np.uint8)

    # Apply a colormap to the imageset (np array)
    heatmap = cv2.applyColorMap(arr8, cv2.COLORMAP_HOT)

    # Convert the BGR colorspace to RGB, this is needed as cv2 works in BGR 
    # colorspace as opposed to RGB colorspace.
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    # Fix as colored images have 3*8 bits = 3 bytes instead of one
    bytes_per_line = np_pixels.shape[1] * 3

    qimage = QtGui.QImage(
        heatmap,
        heatmap.shape[1],
        heatmap.shape[0],
        bytes_per_line,
        QtGui.QImage.Format_RGB888)

    return qimage


def get_pixmaps(pixel_array, window, level, pixmap_aspect,
                fusion=False, color=None):
    """
    Get a dictionary of pixmaps.

    :param pixel_array: A list of converted pixel arrays
    :param window: Window width of windowing function
    :param level: Level value of windowing function
    :param pixmap_aspect: Scaling ratio for axial, coronal, and sagittal pixmaps
    :param fusion: Boolean to determine if pixmaps will be fused
    :param color: String for conversion of pixels to specified color map
    :return: dict_pixmaps, a dictionary of all pixmaps within the patient.
    """
    # Convert pixel array to numpy 3d array
    pixel_array_3d = np.array(pixel_array)

    # Pixmaps dictionaries of 3 views
    dict_pixmaps_axial = {}
    dict_pixmaps_coronal = {}
    dict_pixmaps_sagittal = {}

    axial_width, axial_height = scaled_size(
        pixel_array_3d.shape[1] * pixmap_aspect["axial"],
        pixel_array_3d.shape[2])
    coronal_width, coronal_height = scaled_size(
        pixel_array_3d.shape[1],
        pixel_array_3d.shape[0] *
        pixmap_aspect["coronal"])
    sagittal_width, sagittal_height = scaled_size(
        pixel_array_3d.shape[2] * pixmap_aspect["sagittal"],
        pixel_array_3d.shape[0])

    for i in range(pixel_array_3d.shape[0]):
        dict_pixmaps_axial[i] = scaled_pixmap(
            pixel_array_3d[i, :, :],
            window,
            level,
            axial_width,
            axial_height,
            fusion,
            color)

    for i in range(pixel_array_3d.shape[1]):
        dict_pixmaps_coronal[i] = scaled_pixmap(
            pixel_array_3d[:, i, :],
            window,
            level,
            coronal_width,
            coronal_height,
            fusion,
            color)

    for i in range(pixel_array_3d.shape[2]):
        dict_pixmaps_sagittal[i] = scaled_pixmap(
            pixel_array_3d[:, :, i],
            window,
            level,
            sagittal_width,
            sagittal_height,
            fusion,
            color)

    return dict_pixmaps_axial, dict_pixmaps_coronal, dict_pixmaps_sagittal


def scaled_size(width, height):
    if width > height:
        height = constant.DEFAULT_WINDOW_SIZE / width * height
        width = constant.DEFAULT_WINDOW_SIZE
    else:
        width = constant.DEFAULT_WINDOW_SIZE / height * width
        height = constant.DEFAULT_WINDOW_SIZE
    return width, height
