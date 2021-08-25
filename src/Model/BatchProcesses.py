import os
from src.Model.ISO2ROI import ISO2ROI
from src.Model import ImageLoading
from src.Model import InitialModel

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcess:

    def __init__(self, progress_callback, interrupt_flag, patient_files):
        self.patient_dict_container = PatientDictContainer()
        self.progress_callback = progress_callback
        self.interrupt_flag = interrupt_flag
        self.required_classes = ()
        self.patient_files = patient_files
        self.ready = False

    allowed_classes = {}

    def is_ready(self):
        return self.ready

    def start(self):
        pass

    @classmethod
    def load_images(cls, patient_files, required_classes):
        files = []
        found_classes = set()
        for k, v in patient_files.items():
            if k in cls.allowed_classes:
                files.extend(v.get_files())
                modality_name = cls.allowed_classes.get(k).get('name')
                if modality_name not in found_classes \
                        and modality_name in required_classes:
                    found_classes.add(modality_name)

        class_diff = set(required_classes).difference(found_classes)
        if len(class_diff) > 0:
            print("Skipping dataset. Missing required file(s) {}".format(class_diff))
            return False
        try:
            path = os.path.dirname(os.path.commonprefix(files))  # Gets the common root folder.
            read_data_dict, file_names_dict = cls.get_datasets(files)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer singleton.
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(path, read_data_dict, file_names_dict)

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            rois = ImageLoading.get_roi_info(dataset_rtss)

            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            # Add RTSS values to PatientDictContainer
            patient_dict_container.set("rois", rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        return True

    @classmethod
    def get_datasets(cls, filepath_list):
        read_data_dict = {}
        file_names_dict = {}

        slice_count = 0
        for file in ImageLoading.natural_sort(filepath_list):
            try:
                read_file = dcmread(file)
            except InvalidDicomError:
                pass
            else:
                if read_file.SOPClassUID in cls.allowed_classes:
                    allowed_class = cls.allowed_classes[read_file.SOPClassUID]
                    if allowed_class["sliceable"]:
                        slice_name = slice_count
                        slice_count += 1
                    else:
                        slice_name = allowed_class["name"]
                    read_data_dict[slice_name] = read_file
                    file_names_dict[slice_name] = file

        sorted_read_data_dict, sorted_file_names_dict = \
            ImageLoading.image_stack_sort(read_data_dict, file_names_dict)

        return sorted_read_data_dict, sorted_file_names_dict


class BatchProcessISO2ROI(BatchProcess):
    def __init__(self, progress_callback, interrupt_flag, patient_files):
        super(BatchProcessISO2ROI, self).__init__(progress_callback, interrupt_flag, patient_files)
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('ct', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)

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

    def start(self):
        """
        Goes the the steps of the iso2roi conversion.
        :patient_dict_container: dictionary containing dataset
        """

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return

        self.progress_callback.emit(("Setting up .. ", 30))

        InitialModel.create_initial_model()

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        self.progress_callback.emit(("Performing ISO2ROI .. ", 40))
        dataset_complete = ImageLoading.is_dataset_dicom_rt(self.patient_dict_container.dataset)

        iso2roi = ISO2ROI()
        self.progress_callback.emit(("Performing ISO2ROI .. ", 50))

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not self.patient_dict_container.get("file_rtss"):
                iso2roi.create_new_rtstruct(self.progress_callback)

        # Get isodose levels to turn into ROIs
        isodose_levels = iso2roi.get_iso_levels()

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            return False

        self.progress_callback.emit(("Performing ISO2ROI .. ", 80))
        boundaries = iso2roi.calculate_isodose_boundaries(isodose_levels)

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        iso2roi.generate_roi(boundaries, self.progress_callback)