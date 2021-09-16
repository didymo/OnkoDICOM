from pydicom import dcmread
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessROINameCleaning(BatchProcess):
    """
    This class handles batch processing for the DVH2CSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for CSV2ClinicalDataSR
    allowed_classes = {
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        }
    }

    def __init__(self, progress_callback, interrupt_flag, roi_options):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param roi_options: Dictionary of ROI names and what is to be
                            done to them
        """
        # Call the parent class
        super(BatchProcessROINameCleaning, self).__init__(progress_callback,
                                                          interrupt_flag,
                                                          roi_options)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['rtss']
        self.roi_options = roi_options

    def start(self):
        """
        Goes through the steps of the ROI Name Cleaning process.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped Batch ROI Name Cleaning")
            self.patient_dict_container.clear()
            return False

        step = len(self.roi_options) / 100
        progress = 0

        # Loop through each dataset
        for dataset in self.roi_options:
            # Stop loading
            if self.interrupt_flag.is_set():
                # TODO: convert print to logging
                print("Stopped Batch ROI Name Cleaning")
                self.patient_dict_container.clear()
                return False

            rtss = dcmread(dataset)
            roi_step = len(self.roi_options[dataset]) / step
            progress += roi_step
            self.progress_callback.emit(("Cleaning ROIs...", progress))

            for roi in self.roi_options[dataset]:
                # If ignore
                if roi[1] == 0:
                    continue
                # Rename
                elif roi[1] == 1:
                    self.rename()
                # Delete
                elif roi[1] == 2:
                    self.delete()

    def rename(self):
        """
        Rename an ROI in an RTSS.
        """

    def delete(self):
        """
        Delete an ROI from an RTSS.
        """
