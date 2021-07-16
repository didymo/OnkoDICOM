from skimage import measure

from pathlib import Path
from PySide6 import QtCore, QtWidgets
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)


class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn

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

        contours = {}

        # Calculate boundaries for each isodose level for each slice
        for slider_id in range(slider_min, slider_max):
            contours[slider_id] = []
            z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
            grid = get_dose_grid(rt_plan_dose, float(z))

            isodose_percentages = [10, 25, 50, 75, 80, 85, 90, 95, 100, 105]

            if not (grid == []):
                for sd in isodose_percentages:
                    dose_level = sd * rt_dose_dose / (rt_plan_dose.DoseGridScaling * 10000)
                    contours[slider_id].append(measure.find_contours(grid, dose_level))

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

        # Calculate isodose ROI for each slice, skip if slice has no
        # contour data
        name = ""
        rtss = None
        for i in range(slider_min, slider_max):
            if len(contours[i][0]):
                dataset = patient_dict_container.dataset[i]
                pixlut = patient_dict_container.get("pixluts")[dataset.SOPInstanceUID]
                z_coord = dataset.SliceLocation

                # Calculate points from contours
                curr_slice_uid = patient_dict_container.get("dict_uid")[i]
                dose_pixluts = patient_dict_container.get("dose_pixluts")[curr_slice_uid]
                list_points = []
                if len(contours[i][0][0]):      # TODO: replace 2nd 0 with iso level index
                    for item in contours[i][0][0]:
                        list_points.append([dose_pixluts[0][int(item[1])], dose_pixluts[1][int(item[0])]])

                # Convert the pixel points to RCS points
                points = []
                for i, item in enumerate(list_points):
                    points.append(ROI.pixel_to_rcs(pixlut, round(item[0]), round(item[1])))

                contour_data = []
                for p in points:
                    coords = (p[0], p[1], z_coord)
                    contour_data.append(coords)

                # Transform RCS points into 1D array, append z value
                single_array = []

                for sublist in contour_data:
                    for item in sublist:
                        single_array.append(item)

                # Create the ROI
                name = "ISO-10"
                rtss = ROI.create_roi(dataset_rtss, name, single_array, dataset, "DOSE_REGION")

                # Save the updated rtss
                patient_dict_container.set("dataset_rtss", rtss)
                patient_dict_container.set("rois", ImageLoading.get_roi_info(rtss))

        rtss_directory = str(Path(patient_dict_container.get("file_rtss")))

        confirm_save = QtWidgets.QMessageBox.information(None, "Confirmation",
                                                         "Are you sure you want to save the modified RTSTRUCT file? This will "
                                                         "overwrite the existing file. This is not reversible.",
                                                         QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if confirm_save == QtWidgets.QMessageBox.Yes:
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            self.signal_roi_drawn.emit((rtss, {"draw": name}))
            QtWidgets.QMessageBox.about(None, "File saved", "The RTSTRUCT file has been saved.")
            patient_dict_container.set("rtss_modified", False)
