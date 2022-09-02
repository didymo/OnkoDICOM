from pydicom import dcmread
from src.Model import ROI
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessROINameCleaning(BatchProcess):
    """
    This class handles batch processing for the ROI Name Cleaning process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ROI Name Cleaning
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
            self.summary = "Batch ROI Name Cleaning was interrupted."
            return False

        self.summary = "==Batch ROI Name Cleaning==\n"
        step = len(self.roi_options) / 100
        progress = 0

        # Loop through each dataset
        for roi in self.roi_options:
            # Stop loading
            if self.interrupt_flag.is_set():
                # TODO: convert print to logging
                print("Stopped Batch ROI Name Cleaning")
                self.patient_dict_container.clear()
                self.summary = "Batch ROI Name Cleaning was interrupted."
                return False

            self.summary += "ROI: " + roi + "\n"
            roi_step = len(self.roi_options[roi]) / step
            progress += roi_step
            self.progress_callback.emit(("Cleaning ROIs...", progress))

            # Append dataset locations to summary
            self.summary += "Dataset(s): "
            for ds in self.roi_options[roi]:
                self.summary += ds[2] + ", "
            self.summary += "\n"

            # Loop through each dataset in the ROI
            for info in self.roi_options[roi]:
                # If ignore
                if info[0] == 0:
                    self.summary += "Process: Ignored\n\n"
                    continue
                # Rename
                elif info[0] == 1:
                    old_name = roi
                    new_name = info[1]
                    self.rename(info[2], old_name, new_name)
                    self.summary += "Process: Renamed from \'" + old_name \
                                    + "\' to \'" + new_name + "\'\n\n"
                # Delete
                elif info[0] == 2:
                    name = roi
                    rtss = dcmread(info[2])
                    rtss = ROI.delete_roi(rtss, name)
                    rtss.save_as(info[2])
                    self.summary += "Process: Deleted\n\n"

        return True

    def rename(self, dataset, old_name, new_name):
        """
        Rename an ROI in an RTSS.
        :param dataset: file path of the RT Struct to work on.
        :param old_name: old ROI name to change.
        :param new_name: name to change the ROI to.
        """
        # Load dataset
        rtss = dcmread(dataset)

        # Find ROI with old name
        for sequence in rtss.StructureSetROISequence:
            if sequence.ROIName == old_name:
                roi_id = sequence.ROINumber
                # Change name of ROI to new name
                rtss = ROI.rename_roi(rtss, roi_id, new_name)
                # Save dataset
                rtss.save_as(dataset)

        # Return if not found
        return
