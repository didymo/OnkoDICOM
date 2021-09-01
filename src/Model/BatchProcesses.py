import os

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model import CalculateDVHs
from src.Model import ImageLoading
from src.Model import InitialModel
from src.Model.ISO2ROI import ISO2ROI
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcess:
    """
    This class handles loading files for each patient, and getting
    datasets.
    """

    allowed_classes = {}

    def __init__(self, progress_callback, interrupt_flag, patient_files):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: dictionary of patient files for the
                              current patient.
        """
        self.patient_dict_container = PatientDictContainer()
        self.progress_callback = progress_callback
        self.interrupt_flag = interrupt_flag
        self.required_classes = []
        self.patient_files = patient_files
        self.ready = False

    def is_ready(self):
        """
        Returns the status of the batch process.
        """
        return self.ready

    def start(self):
        """
        Starts the batch process.
        """
        pass

    @classmethod
    def load_images(cls, patient_files, required_classes):
        """
        Loads required datasets for the selected patient.
        :param patient_files: dictionary of classes and patient files.
        :param required_classes: list of classes required for the
                                 selected/current process.
        :return: True if all required datasets found, false otherwise.
        """
        files = []
        found_classes = set()

        # Loop through each item in patient_files
        for key, value in patient_files.items():
            # If the item is an allowed class
            if key in cls.allowed_classes:
                # Add item's files to the files list
                files.extend(value.get_files())

                # Get the modality name
                modality_name = cls.allowed_classes.get(key).get('name')

                # If the modality name is not found_classes, add it
                if modality_name not in found_classes \
                        and modality_name in required_classes:
                    found_classes.add(modality_name)

        # Get the difference between required classes and found classes
        class_diff = set(required_classes).difference(found_classes)

        # If the dataset is missing required files, pass on it
        if len(class_diff) > 0:
            print("Skipping dataset. Missing required file(s) {}"
                  .format(class_diff))
            return False

        # Try to get the datasets from the selected files
        try:
            path = os.path.dirname(os.path.commonprefix(files))
            read_data_dict, file_names_dict = cls.get_datasets(files)
        # Otherwise raise an exception (OnkoDICOM does not support the
        # selected file type)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(path, read_data_dict,
                                                  file_names_dict)

        # If an RT Struct is included, set relevant values in the
        # PatientDictContainer
        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = \
                ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            # Add RT Struct values to PatientDictContainer
            patient_dict_container.set("rois", rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        return True

    @classmethod
    def get_datasets(cls, file_path_list):
        """
        Gets datasets in the passed-in file path.
        :param file_path_list: list of file paths to load datasets from.
        """
        read_data_dict = {}
        file_names_dict = {}

        slice_count = 0
        # For each file in the file path list
        for file in ImageLoading.natural_sort(file_path_list):
            # Try to open it
            try:
                read_file = dcmread(file)
            except InvalidDicomError:
                pass
            else:
                # Update relevant data
                if read_file.SOPClassUID in cls.allowed_classes:
                    allowed_class = cls.allowed_classes[read_file.SOPClassUID]
                    if allowed_class["sliceable"]:
                        slice_name = slice_count
                        slice_count += 1
                    else:
                        slice_name = allowed_class["name"]
                    read_data_dict[slice_name] = read_file
                    file_names_dict[slice_name] = file

        # Get and return read data dict and file names dict
        sorted_read_data_dict, sorted_file_names_dict = \
            ImageLoading.image_stack_sort(read_data_dict, file_names_dict)
        return sorted_read_data_dict, sorted_file_names_dict


class BatchProcessISO2ROI(BatchProcess):
    """
    This class handles batch processing for the ISO2ROI process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ISO2ROI
    allowed_classes = {
        # CT Image
        "1.2.840.10008.5.1.4.1.1.2": {
            "name": "ct",
            "sliceable": True
        },
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
        },
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        """
        # Call the parent class
        super(BatchProcessISO2ROI, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('ct', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)

    def start(self):
        """
        Goes through the steps of the ISO2ROI conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return

        # Update progress
        self.progress_callback.emit(("Setting up...", 30))

        # Initialise
        InitialModel.create_initial_model_batch()

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))
        dataset_complete = ImageLoading.is_dataset_dicom_rt(
            self.patient_dict_container.dataset)

        # Create ISO2ROI object
        iso2roi = ISO2ROI()
        self.progress_callback.emit(("Performing ISO2ROI... ", 50))

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container. Otherwise
            # return
            if not self.patient_dict_container.get("file_rtss"):
                self.progress_callback.emit(("Generating RT Struct", 55))
                iso2roi.create_new_rtstruct(self.progress_callback)

        # Get isodose levels to turn into ROIs
        isodose_levels = \
            iso2roi.get_iso_levels('data/csv/batch_isodoseRoi.csv')

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        # Calculate boundaries
        self.progress_callback.emit(("Calculating boundaries...", 60))
        boundaries = iso2roi.calculate_isodose_boundaries(isodose_levels)

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        # Generate ROIs
        self.progress_callback.emit(("Generating ROIs...", 80))
        iso2roi.generate_roi(boundaries, self.progress_callback)

        # Save new RTSS
        self.progress_callback.emit(("Saving RT Struct...", 90))
        iso2roi.save_rtss()


class BatchProcessDVH2CSV(BatchProcess):
    """
    This class handles batch processing for the DVH2CSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ISO2ROI
    allowed_classes = {
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
        },
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        """
        # Call the parent class
        super(BatchProcessDVH2CSV, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('rtss', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)

    def start(self):
        """
        Goes through the steps of the ISO2ROI conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))
        dataset_complete = ImageLoading.is_dataset_dicom_rt(
            self.patient_dict_container.dataset)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container. Otherwise
            # return
            if not self.patient_dict_container.has_modality("rtss"):
                # TODO: convert to logging
                print("No RT Struct, passing...")
                return
            if not self.patient_dict_container.has_modality('rtdose'):
                # TODO: convert to logging
                print("No RT Dose, returning...")
                return

        # Attempt to get DVH data from RT Dose
        # TODO: implement this once DVH2RTDOSE in main repo
        #self.progress_callback.emit(("Attempting to get DVH from RT Dose...",
        #                             50))

        # Calculate DVH if not in RT Dose
        self.progress_callback.emit(("Calculating DVH...", 60))
        read_data_dict = self.patient_dict_container.dataset
        dataset_rtss = self.patient_dict_container.dataset['rtss']
        dataset_rtdose = self.patient_dict_container.dataset['rtdose']
        rois = self.patient_dict_container.get("rois")
        dict_thickness = ImageLoading.get_thickness_dict(dataset_rtss,
                                                         read_data_dict)
        raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose, rois,
                                         dict_thickness, self.interrupt_flag)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            self.patient_dict_container.clear()
            return False

        # Export DVH to CSV
        self.progress_callback.emit(("Exporting DVH to CSV...", 90))

        # Get path to save to
        path = self.patient_dict_container.path

        # Get patient ID
        patient_id = self.patient_dict_container.dataset['rtss'].PatientID

        # Make CSV directory if it doesn't exist
        if not os.path.isdir(path + '/CSV'):
            os.mkdir(path + '/CSV')

        # Save the DVH to a CSV file
        CalculateDVHs.dvh2csv(raw_dvh, path + "/CSV/", 'DVH_' + patient_id,
                              patient_id)
