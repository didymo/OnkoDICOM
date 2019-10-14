import collections
import sys

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsScene, QGraphicsView, QLabel, QVBoxLayout, QMainWindow
from PyQt5.QtGui import QPainter, QPainterPath, QPolygon, QPolygonF, QColor, QPixmap, QPen, QBrush

from src.Model.CalculateImages import *

from matplotlib import _cntr as cntr


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


def get_dose_pixels(pixlut, doselut, img_ds):
    """Convert dosegrid into pixel values"""

    x = []
    y = []

    # PatientPosition: Describes patient position relative to the equipment
    # Check if patient prone
    if 'p' in img_ds.PatientPosition.lower():
        prone = -1  # Prone
    else:
        prone = 1  # Supine

    # Check if patient feetfirst
    if 'ff' in img_ds.PatientPosition.lower():
        feetfirst = -1  # Feet first
    else:
        feetfirst = 1  # Head first

    # Physical distance (in mm) between the center of each image pixel
    spacing = img_ds.PixelSpacing

    # Formula based on GetDoseGridPixelData function in dicompyler
    # (https://github.com/bastula/dicompyler/blob/master/dicompyler/baseplugins/2dview.py)
    x = (np.array(doselut[0]) - pixlut[0][0]) * \
        prone * feetfirst / spacing[0]
    y = (np.array(doselut[1]) - pixlut[1][0]) * prone / spacing[1]

    return (x, y)


def get_dose_pixluts(dict_ds):
    """Convert dosegrid data for each slice into pixel values

    :param dict_ds:     dictionary containing patient data
    :return:            dictionary with dose pixel values as values and
                        SOPInstanceUID as key
    """

    dict_pixluts = {}
    dict_dose_pixluts = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss']
    dose_data = calculate_matrix(dict_ds['rtdose'])
    for ds in dict_ds:
        if ds not in non_img_type:
            img_ds = dict_ds[ds]
            pixlut = calculate_matrix(img_ds)
            dose_pixlut = get_dose_pixels(pixlut, dose_data, img_ds)
            dict_dose_pixluts[img_ds.SOPInstanceUID] = dose_pixlut

    return dict_dose_pixluts


def get_dose_grid(rtd, z=0):
    """
    Return the 2d dose grid for the given slice position (mm). 
    Based on the function GetDoseGrid in dicompyler-core
    (https://github.com/dicompyler/dicompyler-core/blob/master/dicompylercore/dicomparser.py)

    :param rtd:     Data from RTDose file
    :param z:       Position of slice in mm
    :return:        Dose grid as a 2d numpy array
    """

    if 'GridFrameOffsetVector' in rtd:
        z = float(z)

        planes = rtd.ImageOrientationPatient[0] * np.array(rtd.GridFrameOffsetVector) + \
            rtd.ImagePositionPatient[2]
        frame = -1

        if (np.amin(np.fabs(planes - z)) < 0.5):
            frame = np.argmin(np.fabs(planes - z))
            return rtd.pixel_array[frame]

        if ((z > np.amin(planes)) or (z < np.amax(planes))):
            umin = np.fabs(planes - z)
            lmin = umin.copy()
            ub = np.argmin(umin)

            lmin[ub] = np.amax(umin)
            lb = np.argmin(lmin)

            # Fractional distance from bottom to top
            # Plane is at upper plane if 1, lower plane if 0
            fz = (z - planes[lb]) / (planes[ub] - planes[lb])

            plane = fz * rtd.pixel_array[ub] + \
                (1.0 + fz) * rtd.pixel_array[lb]

            return plane

        return np.array([])


class Test(QWidget):

    def __init__(self, pixmap, dose_pixluts, contours, parent=None):
        QWidget.__init__(self, parent)
        self.label = QLabel()

        self.pixmap = pixmap
        self.label.setPixmap(self.pixmap)

        self.polygons = self.calcPolygonF(dose_pixluts, contours)

        self.scene = QGraphicsScene()
        self.scene.addWidget(self.label)
        for i in range(len(self.polygons)):
            self.scene.addPolygon(self.polygons[i], QPen(
                QColor(122, 163, 39, 128)), QBrush(QColor(122, 163, 39, 128)))
        self.view = QGraphicsView(self.scene)
        self.view.setScene(self.scene)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.show()

    def calcPolygonF(self, dose_pixluts, contours):
        list_polygons = []
        for contour in contours:
            list_qpoints = []
            for point in contour[::3]:
                curr_qpoint = QPoint(
                    dose_pixluts[0][int(point[0])], dose_pixluts[1][int(point[1])])
                list_qpoints.append(curr_qpoint)
            curr_polygon = QPolygonF(list_qpoints)
            list_polygons.append(curr_polygon)
        return list_polygons


if __name__ == '__main__':
    # path = *path_to_directory*
    dict_ds, dict_path = get_datasets(path)

    dict_dose_pixluts = get_dose_pixluts(dict_ds)

    curr_slice = '1.3.12.2.1107.5.1.4.49601.30000017081104561168700001115'
    curr_dose = dict_dose_pixluts[curr_slice]

    app = QApplication(sys.argv)
    z = 0
    for key in dict_ds:
        ds = dict_ds[key]
        if ds.SOPInstanceUID == '1.3.12.2.1107.5.1.4.49601.30000017081104561168700001115':
            ds.convert_pixel_data()
            np_pixels = ds._pixel_array
            pixmap = scaled_pixmap(np_pixels, 1500, 400)
            z = ds.ImagePositionPatient[2]
            break

    grid = get_dose_grid(dict_ds['rtdose'], float(z))

    rxdose = 1

    if dict_ds['rtplan']:
        if dict_ds['rtplan'].DoseReferenceSequence[0].DoseReferenceStructureType:
            rxdose = dict_ds['rtplan'].DoseReferenceSequence[0].TargetPrescriptionDose * 100
        elif dict_ds['rtplan'].FractionGroupSequence:
            fraction_group = dict_ds['rtplan'].FractionGroupSequence[0]
            if ("NumberOfFractionsPlanned" in fraction_group) and \
               ("ReferencedBeamSequence" in fraction_group):
                beams = fraction_group.ReferencedBeamSequence
                number_of_fractions = fraction_group.NumberOfFractionsPlanned
                for beam in beams:
                    if "BeamDose" in beam:
                        rxdose += beam.BeamDose * number_of_fractions * 100
        rxdose = round(rxdose)

    if not (grid == []):
        x, y = np.meshgrid(
            np.arange(grid.shape[1]), np.arange(grid.shape[0]))

        # Instantiate the isodose generator for this slice
        isodosegen = cntr.Cntr(x, y, grid)

        level = 50 * rxdose / (dict_ds['rtdose'].DoseGridScaling * 10000)
        contours = isodosegen.trace(level)
        contours = contours[:len(contours)//2]

    w = Test(pixmap, dict_dose_pixluts[curr_slice], contours)
    app.exec_()
