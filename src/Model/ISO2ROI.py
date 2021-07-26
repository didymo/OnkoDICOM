from PySide6 import QtCore, QtWidgets
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer

from pathlib import Path
from skimage import measure


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)


class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn
        self.isodose_levels = {}

    def get_iso_levels(self):
        """
        Opens /data/csv/isodoseRoi.csv to find the isodose levels that
        the user wants turned into ROIs. Creates a dictionary where the
        key is the isoname, and the value is a list containing a boolean
        (cGy: 0, %: 1) and an integer (cGy/% value).
        """

        # Clear self.isodose_levels (in case ISO2ROI has already been run this session)
        self.isodose_levels = {}

        # Open isodoseRoi.csv
        with open('data/csv/isodoseRoi.csv', "r") as fileInput:
            for row in fileInput:
                items = row.split(',')
                self.isodose_levels[items[2]] = [items[1] == 'cGy', int(items[0])]


    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: coutours, a list containing the countours for each
                 isodose level
        """
        # Initialise variables needed to find isodose levels
        patient_dict_container = PatientDictContainer()
        pixmaps = patient_dict_container.get("pixmaps")
        slider_min = 0
        slider_max = len(pixmaps)

        rt_plan_dose = patient_dict_container.dataset['rtdose']
        rt_dose_dose = patient_dict_container.get("rx_dose_in_cgray")

        # If rt_dose_dose does not exist, return None
        if not rt_dose_dose:
            return None

        contours = {}

        for item in self.isodose_levels:
            # Calculate boundaries for each isodose level for each slice
            contours[item] = []
            for slider_id in range(slider_min, slider_max):
                contours[item].append([])
                z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
                grid = get_dose_grid(rt_plan_dose, float(z))

                if not (grid == []):
                    if self.isodose_levels[item][0]:
                        dose_level = self.isodose_levels[item][1] / \
                                     (rt_plan_dose.DoseGridScaling * 100)
                        contours[item][slider_id] =\
                            (measure.find_contours(grid, dose_level))
                    else:
                        dose_level = self.isodose_levels[item][1] * rt_dose_dose / \
                                     (rt_plan_dose.DoseGridScaling * 10000)
                        contours[item][slider_id] = \
                            (measure.find_contours(grid, dose_level))

        # Return list of contours for each isodose level for each slice
        return contours

    def generate_roi(self, contours):
        """
        Generates new ROIs based on contour data.
        :param contours: dictionary of contours to turn into ROIs
        """
        # Initialise variables needed for function
        patient_dict_container = PatientDictContainer()
        dataset_rtss = patient_dict_container.get("dataset_rtss")
        pixmaps = patient_dict_container.get("pixmaps")
        slider_min = 0
        slider_max = len(pixmaps) - 1

        # Save RTSS if it has been modified but not saved
        if patient_dict_container.get("rtss_modified"):
            rtss_directory = Path(patient_dict_container.get("file_rtss"))
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            patient_dict_container.set("rtss_modified", False)

        # Calculate isodose ROI for each slice, skip if slice has no
        # contour data
        rtss = None

        for item in contours:
            for i in range(slider_min, slider_max):
                if not len(contours[item][i]):
                    continue

                # Get required data for calculating ROI
                dataset = patient_dict_container.dataset[i]
                pixlut = patient_dict_container.get("pixluts")[dataset.SOPInstanceUID]
                z_coord = dataset.SliceLocation
                curr_slice_uid = patient_dict_container.get("dict_uid")[i]
                dose_pixluts = patient_dict_container.get("dose_pixluts")[curr_slice_uid]

                # Loop through each contour for each slice
                list_points = []
                for j in range(len(contours[item][i])):
                    list_points.append([])
                    for point in contours[item][i][j]:
                        list_points[j].append\
                            ([dose_pixluts[0][int(point[1])],
                              dose_pixluts[1][int(point[0])]])

                # Convert the pixel points to RCS points
                points = []
                for i in range(len(list_points)):
                    points.append([])
                    for point in list_points[i]:
                        points[i].append\
                            (ROI.pixel_to_rcs(pixlut,
                                              round(point[0]),
                                              round(point[1])))

                contour_data = []
                for i in range(len(points)):
                    contour_data.append([])
                    for p in points[i]:
                        coords = (p[0], p[1], z_coord)
                        contour_data[i].append(coords)

                # Transform RCS points into 1D array, append z value
                single_array = []
                for i in range(len(contour_data)):
                    single_array.append([])
                    for sublist in contour_data[i]:
                        for point in sublist:
                            single_array[i].append(point)

                # Create the ROI(s)
                for array in single_array:
                    rtss = ROI.create_roi(dataset_rtss, item,
                                          array, dataset, "DOSE_REGION")

                    # Save the updated rtss
                    patient_dict_container.set("dataset_rtss", rtss)
                    patient_dict_container.set("rois",
                                               ImageLoading.get_roi_info(rtss))

            # Emit that a new ROI has been created to update the
            # structures tab
            if rtss:
                self.signal_roi_drawn.emit((rtss, {"draw": item}))

        # Save the new ROIs to the RT Struct file
        rtss_directory = Path(patient_dict_container.get("file_rtss"))

        confirm_save = QtWidgets.QMessageBox.information(None, "Confirmation",
                                                         "Are you sure you want to save the modified RTSTRUCT file? This will "
                                                         "overwrite the existing file. This is not reversible.",
                                                         QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if confirm_save == QtWidgets.QMessageBox.Yes:
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            QtWidgets.QMessageBox.about(None, "File saved", "The RTSTRUCT file has been saved.")
            patient_dict_container.set("rtss_modified", False)
