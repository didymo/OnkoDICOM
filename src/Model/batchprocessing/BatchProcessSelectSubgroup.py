from pathlib import Path
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessSelectSubgroup(BatchProcess):
    """
    This class handles batch processing for the Selecting subgroup
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

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 selected_filters):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param selected_filters: dictionary of keys and lists of valid values
        to filter by in the patients clinical-data-sr file (if one exists)
        """
        # Call the parent class
        super(BatchProcessSelectSubgroup, self).__init__(progress_callback,
                                                         interrupt_flag,
                                                         patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['sr']
        self.ready = self.load_images(patient_files, self.required_classes)
        self.within_filter = False
        self.selected_filters = selected_filters

    def start(self):
        """
        Goes through the steps of the ClinicalData filtering.
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
        self.check_if_patient_meets_filter_criteria(data_dict)
        return True

    def find_clinical_data_sr(self):
        """
        Searches the patient dict container for any SR files containing
        clinical data. Returns the first SR with clinical data found.
        :return: ds, SR dataset containing clinical data, or None if
                 nothing found.
        """
        datasets = self.patient_dict_container.dataset

        if not datasets:
            return None

        for ds in datasets:
            # Check for SR files
            if datasets[ds].SOPClassUID == "1.2.840.10008.5.1.4.1.1.88.33":
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
            value = data_list[row].strip()
            if value == "":
                continue
            # Assumes neither data nor attributes have colons
            row_data = value.split(":")
            data_dict[row_data[0]] = row_data[1][1:]

        return data_dict

    def check_if_patient_meets_filter_criteria(self, data_dict):
        """
        Checks if data_dict from patients clinical data contains a match
        from the selected_filters dictionary.
        :param sr_cd: the patients clinical data SR dataset.
        """
        for filter_attribute, allowed_values in self.selected_filters.items():
            try:
                patient_value = data_dict[filter_attribute]

                if len(allowed_values) == 0:
                    continue

                if patient_value in allowed_values:
                    self.within_filter = True
                    break
            except KeyError:
                # they have an sr file that does not contain this trait
                continue
