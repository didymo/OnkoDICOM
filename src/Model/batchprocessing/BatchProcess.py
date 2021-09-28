import os
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.GetPatientInfo import DicomTree
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
        self.summary = ""

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
                for i in range(len(value)):
                    # Add item's files to the files list
                    files.extend(value[i].get_files())

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
            # Convert paths to a common file system representation
            for i, file in enumerate(files):
                files[i] = Path(file).as_posix()
            read_data_dict, file_names_dict = cls.get_datasets(files)
            path = os.path.dirname(
                os.path.commonprefix(list(file_names_dict.values())))
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
        rtss_found = False
        for file in ImageLoading.natural_sort(file_path_list):
            # Try to open it
            try:
                read_file = dcmread(file)
            except InvalidDicomError:
                continue

            # Update relevant data
            if read_file.SOPClassUID in cls.allowed_classes:
                allowed_class = cls.allowed_classes[read_file.SOPClassUID]
                if allowed_class["sliceable"]:
                    slice_name = slice_count
                    slice_count += 1
                else:
                    slice_name = allowed_class["name"]

                # Here we need to compare DICOM files to get the correct
                # RTSS for the required image, i.e., the RTSS that
                # references the images we want. Once we have found the
                # right RTSS we skip over any other ones.
                if slice_name == 'rtss' and rtss_found:
                    continue

                # Check to see if we have found the right RTSS
                if slice_name == 'rtss' \
                        and "ReferencedFrameOfReferenceSequence" in read_file:
                    ref_frame = read_file.ReferencedFrameOfReferenceSequence
                    if "RTReferencedStudySequence" in ref_frame[0]:
                        ref_study = ref_frame[0].RTReferencedStudySequence[0]
                        if "RTReferencedSeriesSequence" in ref_study:
                            if "SeriesInstanceUID" in \
                                    ref_study.RTReferencedSeriesSequence[0]:
                                ref_series = \
                                    ref_study.RTReferencedSeriesSequence[0]
                                ref_image_series_uid = \
                                    ref_series.SeriesInstanceUID
                                if ref_image_series_uid \
                                        == read_data_dict[0].SeriesInstanceUID:
                                    rtss_found = True

                # Continue if we have found an RTSS but it is not
                # the right one
                if slice_name == 'rtss' and not rtss_found:
                    continue

                # Skip this file if it does not match files already in the
                # dataset, and if this file is an image.
                # TODO: allow selection of which set of images (CT, PET,
                #       etc.) to open (by description). Currently only
                #       opens first set of each found + matching RTSS
                if len(read_data_dict) > 0 \
                        and isinstance(slice_name, int) \
                        and read_file.SeriesInstanceUID \
                        != read_data_dict[0].SeriesInstanceUID:
                    continue

                read_data_dict[slice_name] = read_file
                file_names_dict[slice_name] = file

        # Get and return read data dict and file names dict
        sorted_read_data_dict, sorted_file_names_dict = \
            ImageLoading.image_stack_sort(read_data_dict, file_names_dict)
        return sorted_read_data_dict, sorted_file_names_dict

    @classmethod
    def create_new_rtstruct(cls, progress_callback):
        """
        Generates a new RTSS and edits the patient dict container. Used
        for batch processing.
        """
        # Get common directory
        patient_dict_container = PatientDictContainer()
        file_path = patient_dict_container.filepaths.values()
        file_path = Path(os.path.commonpath(file_path))

        # Get new RT Struct file path
        file_path = str(file_path.joinpath("rtss.dcm"))

        # Create RT Struct file
        progress_callback.emit(("Generating RT Structure Set", 60))
        ct_uid_list = ImageLoading.get_image_uid_list(
            patient_dict_container.dataset)
        ds = ROI.create_initial_rtss_from_ct(
            patient_dict_container.dataset[0], file_path, ct_uid_list)
        ds.save_as(file_path)

        # Add RT Struct file path to patient dict container
        patient_dict_container.filepaths['rtss'] = file_path
        filepaths = patient_dict_container.filepaths

        # Add RT Struct dataset to patient dict container
        patient_dict_container.dataset['rtss'] = ds
        dataset = patient_dict_container.dataset

        # Set some patient dict container attributes
        patient_dict_container.set("file_rtss", filepaths['rtss'])
        patient_dict_container.set("dataset_rtss", dataset['rtss'])

        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss",
                                   dicom_tree_rtss.dict)

        dict_pixluts = ImageLoading.get_pixluts(
            patient_dict_container.dataset)
        patient_dict_container.set("pixluts", dict_pixluts)

        rois = ImageLoading.get_roi_info(ds)
        patient_dict_container.set("rois", rois)

        patient_dict_container.set("selected_rois", [])
        patient_dict_container.set("dict_polygons_axial", {})

        patient_dict_container.set("rtss_modified", True)

    @classmethod
    def save_rtss(cls):
        """
        Saves the RT Struct.
        """
        patient_dict_container = PatientDictContainer()
        rtss_directory = Path(patient_dict_container.get("file_rtss"))
        patient_dict_container.get("dataset_rtss").save_as(rtss_directory)