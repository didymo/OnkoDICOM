import kaplanmeier as km
import matplotlib as mp1
mp1.use("TkAgg")
from matplotlib import pyplot as plt
import pandas as pd
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import logging


class BatchProcessKaplanMeier(BatchProcess):
    """
    This class handles batch processing for the Clinical Data 2 CSV
    process. Inherits from the BatchProcessing class.
    """
    # Allowed classes for ClinicalDataSR2CSV
    allowed_classes = {
        # Comprehensive SR
        "1.2.840.10008.5.1.4.1.1.88.33": {
            "name": "sr",
            "sliceable": False
        }
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files, data_Dict,
                 kaplanmeier_targetCol, kaplanmeier_DurationOfLifeCol, kaplanmeier_AliveOrDeadCol):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: Path of the output CSV file.
        """
        # Call the parent class
        super(BatchProcessKaplanMeier, self).__init__(progress_callback,
                                                             interrupt_flag,
                                                             patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['sr']
        self.ready = self.load_images(patient_files, self.required_classes)
        self.kaplanmeier_targetCol = kaplanmeier_targetCol
        self.kaplanmeier_ = kaplanmeier_targetCol
        self.kaplanmeier_targetCol = kaplanmeier_targetCol
        self.kaplanmeier_DurationOfLifeCol = kaplanmeier_DurationOfLifeCol
        self.kaplanmeier_AliveOrDeadCol = kaplanmeier_AliveOrDeadCol
        self.dataDict = data_Dict

    def start(self):
        """
        Goes through the steps of the ClinicalData-SR2CSV conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        # See if SR contains clinical data
        self.progress_callback.emit(("Checking SR file...", 20))
        cd_sr = self.find_clinical_data_sr()

        if cd_sr is None:
            self.summary = "CD_NO_SR"
            return False

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Read in clinical data from SR
        self.progress_callback.emit(("Reading clinical data...", 50))
        data_dict = self.read_clinical_data_from_sr(cd_sr)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Write clinical data to CSV
        self.progress_callback.emit(("Writing clinical data to CSV...", 80))
        self.plot(data_dict, self.kaplanmeier_targetCol, self.kaplanmeier_DurationOfLifeCol, self.kaplanmeier_AliveOrDeadCol)
        return True

    def find_clinical_data_sr(self):
        """
        Searches the patient dict container for any SR files containing
        clinical data. Returns the first SR with clinical data found.
        :return: ds, SR dataset containing clinical data, or None if
                 nothing found.
        """
        datasets = self.patient_dict_container.dataset

        for ds in datasets:
            # Check for SR files
            if datasets[ds].SOPClassUID == '1.2.840.10008.5.1.4.1.1.88.33':
                # Check to see if it is a clinical data SR
                if datasets[ds].SeriesDescription == "CLINICAL-DATA":
                    return datasets[ds]

        return None

    def read_clinical_data_from_sr(self, sr_cd):
        """
        Reads clinical data from the found SR file.
        :param sr_cd: the clinical data SR dataset.
        :return: dictionary of clinical data, where keys are attributes
                 and values are data.
        """
        data = sr_cd.ContentSequence[0].TextValue

        data_dict = {}

        data_list = data.split("\n")
        for row in range(len(data_list)):
            if data_list[row] == '':
                continue
            # Assumes neither data nor attributes have colons
            row_data = data_list[row].split(":")
            data_dict[row_data[0]] = [row_data[1][1:]]

        return data_dict

    def plot(self,data_dict, target, DurationOfLife, AliveOfDead):
        """
            Creates plot based off input columns
        """
        logging.debug("Plot function called")
        try:
            logging.debug("Creating/Displaying plot")
            # creates dataframe based on patient records
            df = pd.DataFrame.from_dict(self.dataDict)
            # creates input parameters for the km.fit() function
            time_event = df[DurationOfLife]
            censoring = df[AliveOfDead]
            y = df[target]
            # create kaplanmeier plot
            results = km.fit(time_event, censoring, y)
            km.plot(results, cmap='Set1', cii_lines='dense', cii_alpha=0.10)
            # specifies plot layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.903,
                                bottom=0.423,
                                left=0.085,
                                right=0.965,
                                hspace=0.2,
                                wspace=0.2)
            #displays plot
            plt.show()
        except:
            logging.debug("failed to create plot")
            self.summary = "INTERRUPT"
