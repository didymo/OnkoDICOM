from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from skimage import measure

from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer

import os.path


class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.files = []
        self.DICOM_files = {}

    def find_DICOM_files(self):
        """Find all DICOM files in the default directory."""
        total_files = sum([len(files) for root, dirs, files in os.walk(self.file_path)])
        if total_files:
            for root, dirs, files in os.walk(self.file_path, topdown=True):
                for name in files:
                    file_name = os.path.join(root, name)
                    try:
                        dicom_file = dcmread(file_name)
                    except (InvalidDicomError, FileNotFoundError):
                        pass
                    else:
                        self.DICOM_files[file_name] = dicom_file

        print("\nFound %s DICOM files." % len(self.DICOM_files))

    def check_elements(self):
        """
        Checks to see if the DICOM files have certain elements, returning a dictionary of elements and if they exist
        in the DICOM-RT image set.
        :return: elements_present, a dictionary with elements as the key (string) and their presence as the value (bool)
        """
        # Return if there are no DICOM files
        if len(self.DICOM_files) == 0:
            print("Error: no DICOM files.")
            return

        # List of elements we are looking for (SOP Class UIDs and their meanings)
        elements = {
            '1.2.840.10008.5.1.4.1.1.481.3': "RT Struct",
            '1.2.840.10008.5.1.4.1.1.2': "CT Image",
            '1.2.840.10008.5.1.4.1.1.481.2': "RT Dose",
            '1.2.840.10008.5.1.4.1.1.481.5': "RT Plan"
        }

        # Dictionary of present elements
        elements_present = {
            "RT Struct": False, "CT Image": False,
            "RT Dose": False, "RT Plan": False
        }

        # Check each DICOM file to see what it contains
        for dicom_file in self.DICOM_files:
            class_uid = self.DICOM_files[dicom_file]["SOPClassUID"].value
            # Check to see if element is of interest and that we haven't already found it in the DICOM file set
            if class_uid in elements:
                if not elements_present[elements[class_uid]]:
                    elements_present[elements[class_uid]] = True

        # Return elements present in DICOM-RT image set
        return elements_present

    def get_rt_dose_dose(self):
        patient_dict_container = PatientDictContainer()
        return patient_dict_container.get("rx_dose_in_cgray")

    def get_rt_plan_dose(self):
        """
        Selects the prescription dose from an RT Plan DICOM file.
        :return: dataset_rtdose, prescription dose from an RT Plan DICOM file
        """
        patient_dict_container = PatientDictContainer()
        return patient_dict_container.dataset['rtdose']

    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: countours, a list containing the countours for each isodose level
        """
        # Initialise variables needed to find isodose levels
        patient_dict_container = PatientDictContainer()

        #pixmaps = patient_dict_container.get("pixmaps")
        #slider_min = 0
        #slider_max = len(pixmaps) - 1
        # for slider_id in range slider_min, slider_max to get iso contours for every slice

        slider_id = 0 # hardcoded now, temporary
        z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
        dataset_rtdose = self.get_rt_plan_dose()
        grid = get_dose_grid(dataset_rtdose, float(z))

        # hardcoded now, temporary
        isodose_percentages = [107, 105, 100, 95, 90, 80, 70, 60, 30, 10]
        contours = []

        if not (grid == []):
            for sd in sorted(isodose_percentages):
                dose_level = sd * self.get_rt_dose_dose() / (dataset_rtdose.DoseGridScaling * 10000)
                contours.append(measure.find_contours(grid, dose_level))

        return contours
