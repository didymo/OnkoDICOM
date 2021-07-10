from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from skimage import measure

from src.Model import ImageLoading
from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, dict_instanceUID
from src.Model.Isodose import  calculate_rx_dose_in_cgray, get_dose_pixluts, get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.Controller.PathHandler import resource_path

import os.path
import platform
import pydicom


class CheckAttributes:
    """This class is for checking that particular attributes exist within a DICOM-RT image set."""
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

    def get_DICOM_files(self):
        """
        Returns the list of DICOM files.
        :return: List of DICOM files found in self.file_path
        """
        dicom_files = []
        for key in self.DICOM_files:
            dicom_files.append(key)
        return dicom_files

    def get_type(self, DICOM_file):
        """
        Returns the type of data contained within a DICOM file
        :return: string type of data in DICOM file (RT Struct, Ct Image, RT Dose, or RT Plan)
        """
        elements = {
            '1.2.840.10008.5.1.4.1.1.481.3': "RT Struct",
            '1.2.840.10008.5.1.4.1.1.2': "CT Image",
            '1.2.840.10008.5.1.4.1.1.481.2': "RT Dose",
            '1.2.840.10008.5.1.4.1.1.481.5': "RT Plan"
        }

        class_uid = DICOM_file["SOPClassUID"].value
        # Check to see what type of data the given DICOM file holds
        if class_uid in elements:
            return elements[class_uid]
        else:
            return "---"

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


# Temporary - will not be needed once functionality integrated into main program
def create_initial_model():
    """
    This function initializes all the attributes in the PatientDictContainer model required for the operation of the
    main window. This should be called before the main window's components are constructed, but after the initial
    values of the PatientDictContainer instance are set (i.e. dataset and filepaths).
    """
    ##############################
    #  LOAD PATIENT INFORMATION  #
    ##############################
    patient_dict_container = PatientDictContainer()

    dataset = patient_dict_container.dataset
    filepaths = patient_dict_container.filepaths
    patient_dict_container.set("rtss_modified", False)

    if ('WindowWidth' in dataset[0]):
        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if ('WindowCenter' in dataset[0]):
        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter)
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1])
    else:
        level = int(800)

    patient_dict_container.set("window", window)
    patient_dict_container.set("level", level)

    # Check to see if the imageWindowing.csv file exists
    if os.path.exists(resource_path('data/csv/imageWindowing.csv')):
        # If it exists, read data from file into the self.dict_windowing variable
        dict_windowing = {}
        with open(resource_path('data/csv/imageWindowing.csv'), "r") as fileInput:
            next(fileInput)
            dict_windowing["Normal"] = [window, level]
            for row in fileInput:
                # Format: Organ - Scan - Window - Level
                items = [item for item in row.split(',')]
                dict_windowing[items[0]] = [int(items[2]), int(items[3])]
    else:
        # If csv does not exist, initialize dictionary with default values
        dict_windowing = {"Normal": [window, level], "Lung": [1600, -300],
                          "Bone": [1400, 700], "Brain": [160, 950],
                          "Soft Tissue": [400, 800], "Head and Neck": [275, 900]}

    patient_dict_container.set("dict_windowing", dict_windowing)

    pixel_values = convert_raw_data(dataset)
    # currently does not work unless run through main OnkoDICOM program - no idea why
    #pixmaps = get_pixmaps(pixel_values, window, level)
    #patient_dict_container.set("pixmaps", pixmaps)
    patient_dict_container.set("pixel_values", pixel_values)

    basic_info = get_basic_info(dataset[0])
    patient_dict_container.set("basic_info", basic_info)

    patient_dict_container.set("dict_uid", dict_instanceUID(dataset))

    # Set RTSS attributes
    if patient_dict_container.has_modality("rtss"):
        patient_dict_container.set("file_rtss", filepaths['rtss'])
        patient_dict_container.set("dataset_rtss", dataset['rtss'])

        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

        patient_dict_container.set("list_roi_numbers", ordered_list_rois(patient_dict_container.get("rois")))
        patient_dict_container.set("selected_rois", [])

        patient_dict_container.set("dict_polygons", {})

    # Set RTDOSE attributes
    if patient_dict_container.has_modality("rtdose"):
        dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
        patient_dict_container.set("dict_dicom_tree_rtdose", dicom_tree_rtdose.dict)

        patient_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

        patient_dict_container.set("selected_doses", [])
        patient_dict_container.set("rx_dose_in_cgray", 1)  # This will be overwritten if an RTPLAN is present.

    # Set RTPLAN attributes
    if patient_dict_container.has_modality("rtplan"):
        # the TargetPrescriptionDose is type 3 (optional), so it may not be there
        # However, it is preferable to the sum of the beam doses
        # DoseReferenceStructureType is type 1 (value is mandatory),
        # but it can have a value of ORGAN_AT_RISK rather than TARGET
        # in which case there will *not* be a TargetPrescriptionDose
        # and even if it is TARGET, that's no guarantee that TargetPrescriptionDose
        # will be encoded and have a value
        rx_dose_in_cgray = calculate_rx_dose_in_cgray(dataset["rtplan"])
        patient_dict_container.set("rx_dose_in_cgray", rx_dose_in_cgray)

        dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
        patient_dict_container.set("dict_dicom_tree_rtplan", dicom_tree_rtplan.dict)


class PrescriptionDose:
    """This class is for selecting the prescription dose from RT Plan and RT Dose files."""
    def __init__(self, check_attributes):
        # Load test DICOM files
        selected_files = check_attributes.get_DICOM_files()
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            patient_dict_container.set("rois", self.rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        create_initial_model()

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


class CalculateISOBoundaries:
    def __init__(self, prescription_dose):
        self.patient_dict_container = PatientDictContainer()
        self.prescription_dose = prescription_dose

    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: countours, a list containing the countours for each isodose level
        """
        # Initialise variables needed to find isodose levels
        slider_id = 0 # hardcoded now, temporary
        z = self.patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
        dataset_rtdose = self.prescription_dose.get_rt_plan_dose()
        grid = get_dose_grid(dataset_rtdose, float(z))

        # hardcoded now, temporary
        isodose_percentages = [107, 105, 100, 95, 90, 80, 70, 60, 30, 10]
        contours = []

        if not (grid == []):
            for sd in sorted(isodose_percentages):
                dose_level = sd * self.prescription_dose.get_rt_dose_dose() / (dataset_rtdose.DoseGridScaling * 10000)
                contours.append(measure.find_contours(grid, dose_level))

        return contours


if __name__ == "__main__":
    # Load test DICOM files
    if platform.system() == "Windows":
        file_path = "\\test\\testdata\\DICOM-RT-TEST"
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        file_path = "/test/testdata/DICOM-RT-TEST"

    # Get the absolute file path
    file_path = os.path.dirname(os.path.realpath(__file__)) + file_path

    # Create a CheckAttributes object
    check_attributes = CheckAttributes(file_path)

    # Find all DICOM files in file_path and its sub-directories and return the presence of certain elements
    check_attributes.find_DICOM_files()
    present_elements = check_attributes.check_elements()

    # Check to make sure that CT and RTDOSE data is present
    if present_elements["CT Image"] and present_elements["RT Dose"]:
        print("CT and RTDOSE data present in DICOM-RT image set located in %s" % file_path)
    elif present_elements["CT Image"] and not present_elements["RT Dose"]:
        print("CT data present in DICOM-RT image set located in %s" % file_path)
    elif not present_elements["CT Image"] and present_elements["RT Dose"]:
        print("RTDOSE data present in DICOM-RT image set located in %s" % file_path)
    else:
        print("CT and RTDOSE data not present in DICOM-RT image set located in %s" % file_path)

    # Get prescription dose from an RT Plan file
    prescription_dose = PrescriptionDose(check_attributes)
    iso_boundaries = CalculateISOBoundaries(prescription_dose)
    iso_boundaries.calculate_boundaries()
    print("")