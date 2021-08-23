import os
from src.Model.ISO2ROI import ISO2ROI
from src.Model import ImageLoading
from src.Model import InitialModel

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcess:
    def __init__(self, progress_callback, patient_files):
        self.allowed_classes = {}
        self.patient_dict_container = PatientDictContainer()
        self.progress_callback = progress_callback
        self.patient_files = patient_files

    def start(self):
        pass

    def load_images(self, files):
        try:
            path = os.path.dirname(os.path.commonprefix(files))  # Gets the common root folder.
            read_data_dict, file_names_dict = self.get_datasets(files)
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

    def get_datasets(self, filepath_list):
        """
        This function generates two dictionaries: the dictionary of PyDicom
        datasets, and the dictionary of filepaths. These two dictionaries are
        used in the PatientDictContainer model as the class attributes:
        'dataset' and 'filepaths' The keys of both dictionaries are the
        dataset's slice number/RT modality. The values of the read_data_dict are
        PyDicom Dataset objects, and the values of the file_names_dict are
        filepaths pointing to the location of the .dcm file on the user's
        computer.
        :param filepath_list: List of all files to be searched.
        :return: Tuple (read_data_dict, file_names_dict)
        """
        read_data_dict = {}
        file_names_dict = {}

        slice_count = 0
        for file in ImageLoading.natural_sort(filepath_list):
            try:
                read_file = dcmread(file)
            except InvalidDicomError:
                pass
            else:
                if read_file.SOPClassUID in self.allowed_classes:
                    allowed_class = self.allowed_classes[read_file.SOPClassUID]
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
    def __init__(self, progress_callback, patient_files):
        super(BatchProcessISO2ROI, self).__init__(progress_callback, patient_files)

        self.allowed_classes = {
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

        self.patient_dict_container = PatientDictContainer()
        self.load_images(patient_files)
        InitialModel.create_initial_model()

    def start(self):
        """
        Goes the the steps of the iso2roi conversion.
        :patient_dict_container: dictionary containing dataset
        """
        dataset_complete = ImageLoading.is_dataset_dicom_rt(self.patient_dict_container.dataset)
        iso2roi = ISO2ROI()

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not self.patient_dict_container.get("file_rtss"):
                iso2roi.create_new_rtstruct(self.progress_callback)

        # Get isodose levels to turn into ROIs
        isodose_levels = iso2roi.get_iso_levels()

        boundaries = iso2roi.calculate_isodose_boundaries(isodose_levels)

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        iso2roi.generate_roi(boundaries, self.progress_callback)