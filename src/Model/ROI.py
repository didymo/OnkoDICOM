import pydicom
import numpy as np

from src.Model.CalculateDVHs import get_roi_info
from src.Model.LoadPatients import *
import matplotlib.pyplot as plt

import math
import matplotlib.path

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPainterPath, QPolygon, QPolygonF, QColor
from PyQt5.QtCore import Qt, QPoint
import sys

# Delete ROI by name
def delete_roi(rtss, roi_name):
    # ROINumber
    roi_number = -1
    # Delete related StructureSetROISequence element
    for i, elem in enumerate(rtss.StructureSetROISequence):
        if elem.ROIName == roi_name:
            roi_number = rtss.StructureSetROISequence[i].ROINumber
            del rtss.StructureSetROISequence[i]

    # Delete related ROIContourSequence element
    for i, elem in enumerate(rtss.ROIContourSequence):
        if elem.ReferencedROINumber == roi_number:
            del rtss.ROIContourSequence[i]

    # Delete related RTROIObservationsSequence element
    for i, elem in enumerate(rtss.RTROIObservationsSequence):
        if elem.ReferencedROINumber == roi_number:
            del rtss.RTROIObservationsSequence[i]

    return rtss


# Return a dictionary of all the contour points of the ROI, slice by slice (if exists)
# Key: ReferencedSOPInstanceUID, Value: ContourData
# ContourData: It looks like a list of values, but it is composed by many 3-item coordinate sets.
# (x, y, z)
# More Info: https://dicom.innolitics.com/ciods/rt-structure-set/roi-contour/30060039/30060040/30060050
def get_raw_contours(rtss, roi_name):
    # The index of the ROI
    roi_number = -1
    # Create a return dictionary
    dict_contours = {}
    # Get the ROI index, and store it for finding the related ROI contour data
    for i, elem in enumerate(rtss.StructureSetROISequence):
        if roi_name == rtss.StructureSetROISequence[i].ROIName:
            roi_number = rtss.StructureSetROISequence[i].ROINumber
            break
    # Loop among every ROI in the ROI contour sequence
    for roi in rtss.ROIContourSequence:
        # Find the target ROI
        if roi.ReferencedROINumber == roi_number:
            # For each slice which contains the ROI
            for slice in roi.ContourSequence:
                # Get the identifier of current slice (with the ROI)
                # Store it, and use it as the key of the dictionary
                for img_seq in slice.ContourImageSequence:
                    # print(img_seq.ReferencedSOPInstanceUID)
                    SOP_UID = img_seq.ReferencedSOPInstanceUID
                contour_data = slice.ContourData
                dict_contours[SOP_UID] = contour_data

    return dict_contours


# Get the transformation matrix from a IMAGE dataset
def get_transform_matrix(img_ds):
    # Physical distance (in mm) between the center of each image pixel, specified by a numeric pair
    # - adjacent row spacing (delimiter) adjacent column spacing.
    dist_row = img_ds.PixelSpacing[0]
    dist_col = img_ds.PixelSpacing[1]
    # The direction cosines of the first row and the first column with respect to the patient.
    # 6 values inside: [Xx, Xy, Xz, Yx, Yy, Yz]
    orientation = img_ds.ImageOrientationPatient
    # The x, y, and z coordinates of the upper left hand corner
    # (center of the first voxel transmitted) of the image, in mm.
    # 3 values: [Sx, Sy, Sz]
    position = img_ds.ImagePositionPatient

    # Equation C.7.6.2.1-1.
    # https://dicom.innolitics.com/ciods/rt-structure-set/roi-contour/30060039/30060040/30060050
    matrix_M = np.matrix(
        [[orientation[0]*dist_row, orientation[3]*dist_col, 0, position[0]],
         [orientation[1]*dist_row, orientation[4]*dist_col, 0, position[1]],
         [orientation[2]*dist_row, orientation[5]*dist_col, 0, position[2]],
         [0, 0, 0, 1]]
    )
    x = []
    y = []
    for i in range(0, img_ds.Columns):
        i_mat = matrix_M * np.matrix([[i], [0], [0], [1]])
        x.append(float(i_mat[0]))

    for j in range(0, img_ds.Rows):
        j_mat = matrix_M * np.matrix([[0], [j], [0], [1]])
        y.append(float(j_mat[1]))

    return (np.array(x), np.array(y))


def get_matrices(dict_ds):
    # Create a dictionary to store matrices of all slices
    dict_matrices = {}
    for key in dict_ds:
        ds = dict_ds[key]
        if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.2':
            # calculate the matrix for transforming
            pixlut = get_transform_matrix(ds)
            # Store it in the dict with the UID of the slice as the key
            dict_matrices[ds.SOPInstanceUID] = pixlut
    return dict_matrices


def get_contour_pixel_data(pixlut, contour, prone = False, feetfirst = False):
    contour_pixel_data = []

    for i in range(0, len(contour), 3):
        for x, x_val in enumerate(pixlut[0]):
            if(x_val > contour[i] and not prone and not feetfirst):
                break
            elif (x_val < contour[i]):
                if feetfirst or prone:
                    break
        for y, y_val in enumerate(pixlut[1]):
            if (y_val > contour[i+1] and not prone):
                break
            elif (y_val < contour[i+1] and prone):
                break
        contour_pixel_data.append((x, y))
    return contour_pixel_data


def get_contours(dict_ds):
    # Get the rt-structure set dataset
    rtss = dict_ds['rtss']

    # store all the roi names in roi_list
    roi_info = get_roi_info(rtss)
    roi_list = []
    for roi in roi_info:
        roi_list.append(roi_info[roi]['name'])

    # Store all the matrices in curr_matirces dictionary
    curr_matrices = {}
    # for every dataset
    for key in dict_ds:
        ds = dict_ds[key]
        # if it is a img dataset
        if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.2':
            # # if the dataset is having the current roi
            # if ds.SOPInstanceUID in curr_slice_list:

            # calculate the matrix for transforming
            pixlut = get_transform_matrix(ds)
            # Store it in the dict with the UID of the slice as the key
            curr_matrices[ds.SOPInstanceUID] = pixlut

    # for every roi
    for roi_name in roi_list:
        # Get a dict of raw contour data of current roi
        dict_curr = get_raw_contours(rtss, roi_name)
        # Get all the UID of slices which having current ROI
        curr_slice_list = []
        for key in dict_curr:
            curr_slice_list.append(key)
        print(curr_slice_list)

    # dict_raw_contours = get_raw_contours(rtss, roi_name)


def get_roi_list(rtss):
    roi_list = []
    roi_info = get_roi_info(rtss)
    for roi in roi_info:
        roi_list.append(roi_info[roi]['name'])
    return roi_list

# get all the contours of all rois within the patient
# {roi:
#       {slice: raw data}
# }
def get_all_raw_contours(rtss, roi_list):
    dict_raw_contours = {}
    for roi in roi_list:
        curr_roi = get_raw_contours(rtss, roi)
        dict_raw_contours[roi] = curr_roi
    return dict_raw_contours


# get all the transformed contour points slice by slice within a given roi
# input raw_contours is a dictionary of raw data of current roi
# roi is the name of the selected roi
def get_roi_contours(raw_contours, roi, dict_matrices):
    dict_roi_contours = {}
    curr_roi_raw_contours = raw_contours[roi]
    for slice in curr_roi_raw_contours:
        raw = curr_roi_raw_contours[slice]
        pixlut = dict_matrices[slice]
        # Transformed is a list of (x, y) coordinates
        transformed = get_contour_pixel_data(pixlut, raw)
        dict_roi_contours[slice] = transformed
    return dict_roi_contours

def get_transformed_pixel_contours(dict_raw_contours, dict_matrices):

    dict_transformed_pixel_contours = {}
    for roi in dict_raw_contours:
        dict_curr_roi = dict_raw_contours[roi]

        dict_curr = {}
        for slice in dict_curr_roi:
            raw_contour = dict_curr_roi[slice]
            curr_pixlut = dict_matrices[slice]
            transformed_pixel = get_contour_pixel_data(curr_pixlut, raw_contour)
            dict_curr[slice] = transformed_pixel
        dict_transformed_pixel_contours[roi] = dict_curr

    return dict_transformed_pixel_contours


def test():
    path = '../../../dicom_sample'
    dict_ds, dict_path = get_datasets(path)
    rtss = dict_ds['rtss']
    dict_matrices = get_matrices(dict_ds)
    roi_list = get_roi_list(rtss)
    dict_raw_contours = get_all_raw_contours(rtss, roi_list)
    for key in dict_raw_contours:
        print(key)

    ### GTVp is the 10th ROI in the sequence
    # (3006, 0022) ROI Number                          IS: "10"
    # (3006, 0024) Referenced Frame of Reference UID   UI: 1.3.12.2.1107.5.1.4.100020.30000018082923183405900000003
    # (3006, 0026) ROI Name                            LO: 'GTVp'
    # (3006, 0036) ROI Generation Algorithm            CS: 'SEMIAUTOMATIC'

    # (3006, 002a) ROI Display Color IS: ['255', '0', '0']
    # (3006, 0040) Contour Sequence 15 item(s) - ---
    roi_name = 'GTVp'
    GTVp_contour = get_roi_contours(dict_raw_contours, roi_name, dict_matrices)
    print(GTVp_contour)

    qpoints = []
    for key in GTVp_contour:
        contour = GTVp_contour[key]
        for point in contour:
            curr_point = QPoint(point[0], point[1])
            qpoints.append(curr_point)
        break
    polygon = QPolygonF(qpoints)

    return polygon


    # xs = []
    # ys = []
    # for slice in GTVp_contour:
    #     points = GTVp_contour[slice]
    #     for point in points:
    #         xs.append(point[0])
    #         ys.append(511 - point[1])
    #     break
    # plt.scatter(xs, ys)
    # plt.show()
    #
    #
    # temp_list = []
    # for x, y in zip(xs, ys):
    #     temp_list.append([x, y])
    #
    # polygon = np.array(temp_list)
    # left = np.min(polygon, axis=0)
    # right = np.max(polygon, axis=0)
    # x = np.arange(math.ceil(left[0]), math.floor(right[0]) + 1)
    # y = np.arange(math.ceil(left[1]), math.floor(right[1]) + 1)
    # xv, yv = np.meshgrid(x, y, indexing='xy')
    # points = np.hstack((xv.reshape((-1, 1)), yv.reshape((-1, 1))))
    #
    # path = matplotlib.path.Path(polygon)
    # mask = path.contains_points(points)
    # mask.shape = xv.shape
    #
    # plt.plot(xs, ys)
    # plt.show()
    # plt.imshow(mask)
    # plt.show()


class Example(QWidget):

    def __init__(self, polygon):
        super().__init__()
        self.polygon = polygon
        self.initUI()

    def initUI(self):
        self.setGeometry(10, 10, 512, 512)
        self.setWindowTitle('Hi')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setBrush(QColor(122, 163, 39, 128))
        qp.setRenderHint(QPainter.Antialiasing)
        self.drawContour(qp)
        qp.end()

    def drawContour(self, qp):
        path = QPainterPath()
        path.addPolygon(self.polygon)
        path.moveTo(30, 30)
        # path.cubicTo(30, 30, 200, 350, 350, 30)

        qp.drawPath(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    polygon = test()
    ex = Example(polygon)
    sys.exit(app.exec_())



# # This is for get all roi at one time
# # Sooooo slowwwwwww
# def main():
#     path = '../../../dicom_sample'
#     dict_ds, path = get_datasets(path)
#     rtss = dict_ds['rtss']
#     dict_matrices = get_matrices(dict_ds)
#     roi_list = get_roi_list(rtss)
#     dict_raw_contours = get_all_raw_contours(rtss, roi_list)
#     dict_contours = get_transformed_pixel_contours(dict_raw_contours, dict_matrices)
#     # print(roi_list)
#
#     f = open("/home/xudong/Desktop/dict.txt", "w")
#     f.write(str(dict_contours))
#     f.close()
#


# def main():
#     path = '../../../dicom_sample'
#     dict_ds, path = get_datasets(path)
#     rtss = dict_ds['rtss']
#
#     get_contours(dict_ds)
#     ### GTVp is the 10th ROI in the sequence
#     # (3006, 0022) ROI Number                          IS: "10"
#     # (3006, 0024) Referenced Frame of Reference UID   UI: 1.3.12.2.1107.5.1.4.100020.30000018082923183405900000003
#     # (3006, 0026) ROI Name                            LO: 'GTVp'
#     # (3006, 0036) ROI Generation Algorithm            CS: 'SEMIAUTOMATIC'
#
#     # (3006, 002a) ROI Display Color IS: ['255', '0', '0']
#     # (3006, 0040) Contour Sequence 15 item(s) - ---
#
#     roi_name = 'EYE_L'
#
#     dict_contours = get_raw_contours(rtss, roi_name)
#
#     roi_slice_list = []
#
#     # Get all the slice UID which contains the ROI
#     for key in dict_contours:
#         roi_slice_list.append(key)
#         # print(key)
#
#     dict_transform_matrices = {}
#
#     for key in dict_ds:
#         ds = dict_ds[key]
#         if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.2':
#             if ds.SOPInstanceUID in roi_slice_list:
#                 pixlut = get_transform_matrix(ds)
#                 dict_transform_matrices[ds.SOPInstanceUID] = pixlut
#
#     pixel_contours = []
#     for key in dict_transform_matrices:
#         contour = dict_contours[key]
#         pixlut = dict_transform_matrices[key]
#         contour_pixel_data = get_contour_pixel_data(pixlut, contour)
#         # print(contour_pixel_data)
#         pixel_contours.append(contour_pixel_data)
#     print(len(pixel_contours))
#     xs = []
#     ys = []
#     for point in pixel_contours[8]:
#         xs.append(point[0])
#         ys.append(511 - point[1])
#     plt.scatter(xs, ys)
#     plt.show()
#
#
#     temp_list = []
#     for x, y in zip(xs, ys):
#         temp_list.append([x, y])
#
#     polygon = np.array(temp_list)
#     left = np.min(polygon, axis=0)
#     right = np.max(polygon, axis=0)
#     x = np.arange(math.ceil(left[0]), math.floor(right[0]) + 1)
#     y = np.arange(math.ceil(left[1]), math.floor(right[1]) + 1)
#     xv, yv = np.meshgrid(x, y, indexing='xy')
#     points = np.hstack((xv.reshape((-1, 1)), yv.reshape((-1, 1))))
#
#     path = matplotlib.path.Path(polygon)
#     mask = path.contains_points(points)
#     mask.shape = xv.shape
#
#     plt.plot(xs, ys)
#     plt.show()
#     plt.imshow(mask)
#     plt.show()