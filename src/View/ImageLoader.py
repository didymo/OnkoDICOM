import os
import platform
from pathlib import Path

from PySide6 import QtCore
from pydicom import dcmread, dcmwrite

from src.Model import ImageLoading
from src.Model.CalculateDVHs import dvh2rtdose, rtdose2dvh, create_initial_rtdose_from_ct
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import create_initial_rtss_from_ct
from src.Model.xrRtstruct import create_initial_rtss_from_cr
from src.Model.GetPatientInfo import DicomTree


class ImageLoader(QtCore.QObject):
    """
    This class is responsible for initializing and creating all the values
    required to create an instance of the PatientDictContainer, that is used
    to store all the DICOM-related data used to create the patient window.
    """

    signal_request_calc_dvh = QtCore.Signal()

    def __init__(self, selected_files, existing_rtss, parent_window,
                 *args, **kwargs):
        super(ImageLoader, self).__init__(*args, **kwargs)
        self.selected_files = selected_files
        self.parent_window = parent_window
        self.existing_rtss = existing_rtss
        self.calc_dvh = False
        self.advised_calc_dvh = False

    def load(self, interrupt_flag, progress_callback):
        """
        :param interrupt_flag: A threading.Event() object that tells the
        function to stop loading. :param progress_callback: A signal that
        receives the current progress of the loading. :return:
        PatientDictContainer object containing all values related to the
        loaded DICOM files.
        """
        progress_callback.emit(("Creating datasets...", 0))
        try:
            # Gets the common root folder.
            path = os.path.dirname(os.path.commonprefix(self.selected_files))
            read_data_dict, file_names_dict = ImageLoading.get_datasets(
                self.selected_files)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer singleton.
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(
            path,
            read_data_dict,
            file_names_dict,
            existing_rtss_files=self.existing_rtss
        )

        # As there is no way to interrupt a QRunnable, this method must
        # check after every step whether or not the interrupt flag has been
        # set, in which case it will interrupt this method after the
        # currently processing function has finished running. It's not very
        # pretty, and the thread will still run some functions for, in some
        # cases, up to a couple seconds after the close button on the
        # Progress Window has been clicked, however it's the best solution I
        # could come up with. If you have a cleaner alternative, please make
        # your contribution.
        if interrupt_flag.is_set():
            print("stopped")
            return False

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            progress_callback.emit(("Getting ROI info...", 10))
            rois = ImageLoading.get_roi_info(dataset_rtss)

            if interrupt_flag.is_set():  # Stop loading.
                return False

            progress_callback.emit(("Getting contour data...", 30))
            dict_raw_contour_data, dict_numpoints = \
                ImageLoading.get_raw_contour_data(dataset_rtss)

            # Determine which ROIs are one slice thick
            dict_thickness = ImageLoading.get_thickness_dict(
                dataset_rtss, read_data_dict)

            if interrupt_flag.is_set():  # Stop loading.
                return False

            progress_callback.emit(("Getting pixel LUTs...", 50))
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            if interrupt_flag.is_set():  # Stop loading.
                return False

            # Add RTSS values to PatientDictContainer
            patient_dict_container.set("rois", rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

            if 'rtdose' not in file_names_dict:
                self.load_temp_rtdose(path,progress_callback,interrupt_flag)

            if 'rtdose' in file_names_dict:
                # Check to see if DVH data exists in the RT Dose. If
                # it is there, return (it will be populated later). If
                # not, ask if the user wants it calculated.
                try:
                    dvh_data = rtdose2dvh()
                    if bool(dvh_data) and not dvh_data["diff"]:
                        return True
                except KeyError:
                    pass

                self.parent_window.signal_advise_calc_dvh.connect(
                    self.update_calc_dvh)
                self.signal_request_calc_dvh.emit()

                while not self.advised_calc_dvh:
                    pass

                # Calculate DVHs
                if self.calc_dvh:
                    dataset_rtdose = dcmread(file_names_dict['rtdose'])

                    # Spawn-based platforms (i.e Windows and MacOS) have
                    # a large overhead when creating a new process, which
                    # ends up making multiprocessing on these platforms more
                    # expensive than linear calculation. As such,
                    # multiprocessing is only available on Linux until a better
                    # solution is found.
                    fork_safe_platforms = ['Linux']
                    if platform.system() in fork_safe_platforms:
                        progress_callback.emit(("Calculating DVHs...", 60))
                        raw_dvh = \
                            ImageLoading.multi_calc_dvh(dataset_rtss,
                                                        dataset_rtdose, rois,
                                                        dict_thickness)
                    else:
                        progress_callback.emit(
                            ("Calculating DVHs... (This may take a while)",
                             60))
                        raw_dvh = \
                            ImageLoading.calc_dvhs(dataset_rtss,
                                                   dataset_rtdose, rois,
                                                   dict_thickness,
                                                   interrupt_flag)

                    if interrupt_flag.is_set():  # Stop loading.
                        return False

                    progress_callback.emit(("Converging to zero...", 80))
                    dvh_x_y = ImageLoading.converge_to_0_dvh(raw_dvh)

                    if interrupt_flag.is_set():  # Stop loading.
                        return False

                    # Add DVH values to PatientDictContainer
                    patient_dict_container.set("raw_dvh", raw_dvh)
                    patient_dict_container.set("dvh_x_y", dvh_x_y)
                    patient_dict_container.set("dvh_outdated", False)

                    # Write DVH data to the RT Dose
                    dvh2rtdose(raw_dvh)

                    return True
        else:
            self.load_temp_rtss(path, progress_callback, interrupt_flag)

        return True

    def load_temp_rtss(self, path, progress_callback, interrupt_flag):
        """
        Generate a temporary rtss and load its data into
        PatientDictContainer
        :param path: str. The common root folder of all DICOM files.
        :param progress_callback: A signal that receives the current
        progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
        function to stop loading.
        """
        progress_callback.emit(("Generating temporary rtss...", 20))
        patient_dict_container = PatientDictContainer()
        rtss_path = Path(path).joinpath('rtss.dcm')
        uid_list = ImageLoading.get_image_uid_list(
            patient_dict_container.dataset)

        if patient_dict_container.dataset[0].Modality == 'CR':
            # XR files
            rtss = create_initial_rtss_from_cr(
                patient_dict_container.dataset[0], rtss_path, uid_list)
            # Code for saving the file automatically
            #rtss_path = patient_dict_container.filepaths[0] + "_XR-RTSTRUCT"
            #rtss.save_as(rtss_path)
        else:
            rtss = create_initial_rtss_from_ct(
                patient_dict_container.dataset[0], rtss_path, uid_list)

        if interrupt_flag.is_set():  # Stop loading.
            print("stopped")
            return False

        progress_callback.emit(("Loading temporary rtss...", 50))
        # Set ROIs
        rois = ImageLoading.get_roi_info(rtss)
        patient_dict_container.set("rois", rois)

        # Set pixluts
        dict_pixluts = ImageLoading.get_pixluts(patient_dict_container.dataset)
        patient_dict_container.set("pixluts", dict_pixluts)

        # Add RT Struct file path and dataset to patient dict container
        patient_dict_container.filepaths['rtss'] = rtss_path
        patient_dict_container.dataset['rtss'] = rtss

        # Set some patient dict container attributes
        patient_dict_container.set("file_rtss", rtss_path)
        patient_dict_container.set("dataset_rtss", rtss)
        ordered_dict = DicomTree(None).dataset_to_dict(rtss)
        patient_dict_container.set("dict_dicom_tree_rtss", ordered_dict)
        patient_dict_container.set("selected_rois", [])


    def load_temp_rtdose(self, path, progress_callback, interrupt_flag):
        """
        Generate a temporary rtdose and load its data into
        PatientDictContainer
        :param path: str. The common root folder of all DICOM files.
        :param progress_callback: A signal that receives the current
        progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
        function to stop loading.
        """
        progress_callback.emit(("Generating temporary rtdose...", 20))
        patient_dict_container = PatientDictContainer()
        rtdose_path = Path(path).joinpath('rtdose.dcm')
        if patient_dict_container.dataset[0].Modality == 'CR':
            print("Unable to generate temporary RT Dose based on CR image")
            return False
        
        uid_list = ImageLoading.get_image_uid_list(
            patient_dict_container.dataset)

        

        rtdose = create_initial_rtdose_from_ct(patient_dict_container.dataset[0], rtdose_path, uid_list)

        if interrupt_flag.is_set():  # Stop loading.
            print("stopped")
            return False

        progress_callback.emit(("Loading temporary rtdose...", 50))
        # Set ROIs
        
        # rois = ImageLoading.get_roi_info(rtdose)
        # patient_dict_container.set("rois", rois)

        # Set pixluts
        dict_pixluts = ImageLoading.get_pixluts(patient_dict_container.dataset)
        patient_dict_container.set("pixluts", dict_pixluts)

        # write the half baked RT Dose to file so future business logic will find it.
        dcmwrite(rtdose_path,rtdose,False)
        # Add RT Dose file path and dataset to patient dict container
        patient_dict_container.filepaths['rtdose'] = rtdose_path
        patient_dict_container.dataset['rtdose'] = rtdose

        # Set some patient dict container attributes
        patient_dict_container.set("file_rtdose", rtdose_path)
        patient_dict_container.set("dataset_rtdose", rtdose)
        ordered_dict = DicomTree(None).dataset_to_dict(rtdose)
        patient_dict_container.set("dict_dicom_tree_rtdose", ordered_dict)
        # patient_dict_container.set("selected_rois", [])


    def update_calc_dvh(self, advice):
        self.advised_calc_dvh = True
        self.calc_dvh = advice
