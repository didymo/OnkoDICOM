import os

from src.Model import CalculateDVHs
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess


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
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

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
            print("Stopped DVH2CSV")
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
