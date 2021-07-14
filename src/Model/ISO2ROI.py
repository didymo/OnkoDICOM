from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from skimage import measure

from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer

import os.path


class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""

    def get_rt_dose_dose(self):
        patient_dict_container = PatientDictContainer()
        return patient_dict_container.get("rx_dose_in_cgray")

    def get_rt_plan_dose(self):
        """
        Selects the prescription dose from an RT Plan DICOM file.
        :return: dataset_rtdose, prescription dose from an RT Plan file
        """
        patient_dict_container = PatientDictContainer()
        return patient_dict_container.dataset['rtdose']

    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: countours, a list containing the countours for each
                 isodose level
        """
        # Initialise variables needed to find isodose levels
        patient_dict_container = PatientDictContainer()

        #pixmaps = patient_dict_container.get("pixmaps")
        #slider_min = 0
        #slider_max = len(pixmaps) - 1
        # for slider_id in range slider_min, slider_max to get iso
        # contours for every slice

        slider_id = 0 # hardcoded now, temporary
        z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
        dataset_rtdose = self.get_rt_plan_dose()
        grid = get_dose_grid(dataset_rtdose, float(z))

        # hardcoded now, temporary
        isodose_percentages = [107, 105, 100, 95, 90, 80, 70, 60, 30, 10]
        contours = []

        if not (grid == []):
            for sd in sorted(isodose_percentages):
                dose_level = sd * self.get_rt_dose_dose() / \
                             (dataset_rtdose.DoseGridScaling * 10000)
                contours.append(measure.find_contours(grid, dose_level))

        return contours
