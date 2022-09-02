import csv
from pydicom import dcmread
from src.Controller.PathHandler import data_path
from src.Model import ROI
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessFMAID2ROIName(BatchProcess):
    """
    This class handles batch processing for the FMA ID to ROI name process.
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
        super(BatchProcessFMAID2ROIName, self).__init__(progress_callback,
                                                        interrupt_flag,
                                                        patient_files)

        # Set class variables
        self.required_classes = ['rtss']
        self.organ_names = {}
        self.fma_ids = []
        self.ready = self.load_images(patient_files, self.required_classes)
        self.patient_dict_container = PatientDictContainer()

    def start(self):
        """
        Goes through the steps of the ROI Name Cleaning process.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Lookup ROI names in Organ List
        self.progress_callback.emit(("Reading ROIs...", 40))
        roi_names = self.find_fma_ids()

        # Return false if RTSS has no ROIs
        if not roi_names:
            self.summary = "ROI_NO_FMA"
            return False

        # Convert FMA ID to ROI name 
        rtss = self.patient_dict_container.dataset['rtss']
        total = 0
        progress = 40
        step = (90 - 40)/len(roi_names)
        for fmaid in roi_names:
            self.progress_callback.emit(("Renaming FMAs...", progress))
            progress += step
            rtss = self.rename(rtss, fmaid, self.organ_names[fmaid])
            total += 1

        rtss.save_as(self.patient_dict_container.filepaths['rtss'])

        # Set the summary to be the number of ROIs modified and return
        self.summary = "FMA_ID_" + str(total)
        return True

    def find_fma_ids(self):
        """
        Return a list of ROI names in the RTSS that are standard organ names.
        :return: list of ROI names.
        """
        # Get organ names and FMA IDs if they have not been populated
        if not self.fma_ids:
            # Get standard organ names
            with open(data_path('organName.csv'), 'r') as f:
                csv_input = csv.reader(f)
                header = next(f)  # Ignore the "header" of the column
                for row in csv_input:
                    self.fma_ids.append(row[1])
                    self.organ_names[row[1]] = row[0]
                f.close()

        rtss = self.patient_dict_container.dataset['rtss']
        rois = []
        # Loop through each ROI in the RT Struct
        for i in range(len(rtss.StructureSetROISequence)):
            # Get the ROI name
            roi_name = rtss.StructureSetROISequence[i].ROIName

            # Add ROI name to the list
            if roi_name in self.fma_ids:
                rois.append(roi_name)

        return rois

    def rename(self, rtss, old_name, new_name):
        """
        Rename an ROI in an RTSS.
        :param rtss: RTSS dataset.
        :param old_name: old ROI name to change.
        :param new_name: name to change the ROI to.
        :return: the new RTSS.
        """
        # Find ROI with old name
        roi_id = None
        for sequence in rtss.StructureSetROISequence:
            if sequence.ROIName == old_name:
                roi_id = sequence.ROINumber
                break

        # Return if not found
        if not roi_id:
            return

        # Change name of ROI to new name
        rtss = ROI.rename_roi(rtss, roi_id, new_name)

        return rtss
