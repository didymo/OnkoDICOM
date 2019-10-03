import collections
import sys

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsScene, QGraphicsView, QLabel, QVBoxLayout, QMainWindow
from PyQt5.QtGui import QPainter, QPainterPath, QPolygon, QPolygonF, QColor, QPixmap, QPen, QBrush


from src.Model.CalculateImages import *

# Get raw contour data of ROI in RT Structure Set
def get_raw_ContourData(rtss):
    # Retrieve a dictionary of ROIName & ROINumber pairs
    dict_id = {}
    for i, elem in enumerate(rtss.StructureSetROISequence):
        roi_number = elem.ROINumber
        roi_name = elem.ROIName
        dict_id[roi_number] = roi_name
    print(dict_id)

    dict_ROI = {}
    for roi in rtss.ROIContourSequence:
        ROIDisplayColor = roi.ROIDisplayColor
        ReferencedROINumber = roi.ReferencedROINumber
        ROIName = dict_id[ReferencedROINumber]
        dict_contour = collections.defaultdict(list)
        for slice in roi.ContourSequence:
            for contour_img in slice.ContourImageSequence:
                ReferencedSOPInstanceUID = contour_img.ReferencedSOPInstanceUID
            ContourGeometricType = slice.ContourGeometricType
            NumberOfContourPoints = slice.NumberOfContourPoints
            ContourData = slice.ContourData
            dict_contour[ReferencedSOPInstanceUID].append(ContourData)
        dict_ROI[ROIName] = dict_contour
    return dict_ROI
    # print(dict_ROI['REST_COMMON LUNG']['1.3.12.2.1107.5.1.4.49601.30000017081104561168700001084'])
    # print(len(dict_ROI['REST_COMMON LUNG']['1.3.12.2.1107.5.1.4.49601.30000017081104561168700001084']))


def calculate_matrix(img_ds):
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
        [[orientation[0] * dist_row, orientation[3] * dist_col, 0, position[0]],
         [orientation[1] * dist_row, orientation[4] * dist_col, 0, position[1]],
         [orientation[2] * dist_row, orientation[5] * dist_col, 0, position[2]],
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


def get_pixluts(dict_ds):
    dict_pixluts = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss']
    for ds in dict_ds:
        if ds not in non_img_type:
            img_ds = dict_ds[ds]
            pixlut = calculate_matrix(img_ds)
            dict_pixluts[img_ds.SOPInstanceUID] = pixlut
    return dict_pixluts


def calculate_pixels(pixlut, contour, prone=False, feetfirst=False):
    pixels = []
    for i in range(0, len(contour), 3):
        for x, x_val in enumerate(pixlut[0]):
            if (x_val > contour[i] and not prone and not feetfirst):
                break
            elif (x_val < contour[i]):
                if feetfirst or prone:
                    break
        for y, y_val in enumerate(pixlut[1]):
            if (y_val > contour[i + 1] and not prone):
                break
            elif (y_val < contour[i + 1] and prone):
                break
        pixels.append([x, y])
    return pixels


# Get pixels of contours of all rois selected within current slice
# Return:
# {slice: list of pixels of all contours in this slice}
def get_contour_pixel(dict_raw_ContourData, roi_selected, dict_pixluts, curr_slice):
    dict_pixels = {}
    pixlut = dict_pixluts[curr_slice]
    for roi in roi_selected:
        dict_pixels_of_roi = collections.defaultdict(list)
        raw_contours = dict_raw_ContourData[roi]
        number_of_contours = len(raw_contours[curr_slice])
        for i in range(number_of_contours):
            contour_pixels = calculate_pixels(pixlut, raw_contours[curr_slice][i])
            dict_pixels_of_roi[curr_slice].append(contour_pixels)
        dict_pixels[roi] = dict_pixels_of_roi
    # print(dict_pixels)
    return dict_pixels


class ContourItem(QtWidgets.QGraphicsScene):
    def __init__(self, dict_rois_contours, roi_selected, curr_slice):
        super(ContourItem, self).__init__()
        self.addPolygon()


class Test(QWidget):

    def __init__(self, pixmap, dict_rois_contours, roi_selected, curr_slice, parent=None):
        QWidget.__init__(self, parent)
        self.label = QLabel()

        self.pixmap = pixmap
        self.dict_rois_contours = dict_rois_contours
        self.curr_roi = roi_selected[0]
        self.curr_slice = curr_slice

        self.label.setPixmap(self.pixmap)

        self.polygons = self.calcPolygonF(self.curr_roi)

        self.scene = QGraphicsScene()
        self.scene.addWidget(self.label)
        for i in range(len(self.polygons)):
            self.scene.addPolygon(self.polygons[i], QPen(QColor(122, 163, 39, 128)), QBrush(QColor(122, 163, 39, 128)))
        self.view = QGraphicsView(self.scene)
        self.view.setScene(self.scene)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show()

    def calcPolygonF(self, curr_roi):
        list_polygons = []
        pixel_list = self.dict_rois_contours[curr_roi][self.curr_slice]
        for i in range(len(pixel_list)):
            list_qpoints = []
            contour = pixel_list[i]
            for point in contour:
                curr_qpoint = QPoint(point[0], point[1])
                list_qpoints.append(curr_qpoint)
            curr_polygon = QPolygonF(list_qpoints)
            list_polygons.append(curr_polygon)
        return list_polygons


# class Widget(QWidget):
#
#     def __init__(self, pixmap):
#         QWidget.__init__(self)
#         self.pixmap = pixmap
#         self.initUI()
#
#     def initUI(self):
#         self.resize(512,512)
#         self.setWindowTitle('DICOM')
#         self.label = QLabel(self)
#         self.label.setPixmap(self.pixmap)
#         self.scene = QGraphicsScene()
#         # Add polygon found here
#         self.scene.addWidget(self.label)
#         self.view = QGraphicsView()
#         self.view.setScene(self.scene)



# class Example(QWidget):
#     def __init__(self, dict_rois_contours, roi_selected, curr_slice):
#         super().__init__()
#         self.dict_rois_contours = dict_rois_contours
#         # print(self.dict_rois_contours)
#         self.roi_selected = roi_selected
#         self.curr_slice = curr_slice
#         self.polygons = self.calcPolygonF(roi_selected[0])
#         self.initUI()
#
#     def initUI(self):
#         self.setGeometry(10, 10, 512, 512)
#         self.setWindowTitle('Multi')
#         self.show()
#
#     def paintEvent(self, e):
#         qp = QPainter()
#         qp.begin(self)
#         qp.setBrush(QColor(122, 163, 39, 128))
#         qp.setRenderHint(QPainter.Antialiasing)
#         self.drawContour(qp)
#         qp.end()
#
#     def calcPolygonF(self, curr_roi):
#         list_polygons = []
#         pixel_list = self.dict_rois_contours[curr_roi][self.curr_slice]
#         for i in range(len(pixel_list)):
#             list_qpoints = []
#             contour = pixel_list[i]
#             for point in contour:
#                 curr_qpoint = QPoint(point[0], point[1])
#                 list_qpoints.append(curr_qpoint)
#             curr_polygon = QPolygonF(list_qpoints)
#             list_polygons.append(curr_polygon)
#         return list_polygons
#
#     def drawContour(self, qp):
#         curr_roi = 'REST_COMMON_LUNG'
#         for i in range(len(self.polygons)):
#             painter_path = QPainterPath()
#             painter_path.addPolygon(self.polygons[i])
#             qp.drawPath(painter_path)

#
# def main():
#     path = '/home/xudong/Desktop/RawDICOM.India-20191001T080723Z-001/RawDICOM.India'
#     dict_ds, dict_path = get_datasets(path)
#     rtss = dict_ds['rtss']
#     dict_raw_ContourData = get_raw_ContourData(rtss)
#     dict_pixluts = get_pixluts(dict_ds)
#     roi_selected = ['REST_COMMON LUNG']
#     curr_slice = '1.3.12.2.1107.5.1.4.49601.30000017081104561168700001115'
#     # Contours of selected ROIs within current slice
#     dict_rois_contours = get_contour_pixel(dict_raw_ContourData, roi_selected, dict_pixluts, curr_slice)
#     xs = []
#     ys = []
#     for roi in roi_selected:
#         lists = dict_rois_contours[roi][curr_slice]
#         print(len(lists))
#         for list in lists:
#             print(list)
#             for point in list:
#                 xs.append(point[0])
#                 ys.append(point[1])
#     plt.scatter(xs, ys)
#     plt.show()
#
#
#     app = QApplication(sys.argv)
#     ex1 = Example(dict_rois_contours, roi_selected, curr_slice)
#     sys.exit(app.exec_())

if __name__ == '__main__':
    path = '/home/xudong/Desktop/RawDICOM.India-20191001T080723Z-001/RawDICOM.India'
    dict_ds, dict_path = get_datasets(path)
    rtss = dict_ds['rtss']
    dict_raw_ContourData = get_raw_ContourData(rtss)
    dict_pixluts = get_pixluts(dict_ds)
    roi_selected = ['REST_COMMON LUNG']
    curr_slice = '1.3.12.2.1107.5.1.4.49601.30000017081104561168700001115'
    # Contours of selected ROIs within current slice
    dict_rois_contours = get_contour_pixel(dict_raw_ContourData, roi_selected, dict_pixluts, curr_slice)
    # xs = []
    # ys = []
    # for roi in roi_selected:
    #     lists = dict_rois_contours[roi][curr_slice]
    #     print(len(lists))
    #     for list in lists:
    #         print(list)
    #         for point in list:
    #             xs.append(point[0])
    #             ys.append(point[1])
    # plt.scatter(xs, ys)
    # plt.show()

    app = QApplication(sys.argv)

    for key in dict_ds:
        ds = dict_ds[key]
        if ds.SOPInstanceUID == '1.3.12.2.1107.5.1.4.49601.30000017081104561168700001115':
            ds.convert_pixel_data()
            np_pixels = ds._pixel_array
            print('HIT')
            pixmap = scaled_pixmap(np_pixels, 1500, 400)
            break


    print(dict_ds[1])



    # app = QApplication(sys.argv)
    # ex1 = Example(dict_rois_contours, roi_selected, curr_slice)
    # app.exec_()

    w = Test(pixmap, dict_rois_contours, roi_selected, curr_slice)
    app.exec_()