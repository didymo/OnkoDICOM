from src.Model import InitialModel
from src.Model import ImageLoading
from src.Model.ISO2ROI import ISO2ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess


class BatchProcessISO2ROI(BatchProcess):
    """
    This class handles batch processing for the ISO2ROI process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ISO2ROI
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
        # RT Plan
        "1.2.840.10008.5.1.4.1.1.481.5": {
            "name": "rtplan",
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
        super(BatchProcessISO2ROI, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('ct', 'rtdose', 'rtplan')
        self.ready = self.load_images(patient_files, self.required_classes)

    def start(self):
        """
        Goes through the steps of the ISO2ROI conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        # Update progress
        self.progress_callback.emit(("Setting up...", 30))

        # Initialise
        InitialModel.create_initial_model_batch()

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))
        dataset_complete = ImageLoading.is_dataset_dicom_rt(
            self.patient_dict_container.dataset)

        # Create ISO2ROI object
        iso2roi = ISO2ROI()
        self.progress_callback.emit(("Performing ISO2ROI... ", 50))

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container. Otherwise
            # return
            if not self.patient_dict_container.get("file_rtss"):
                self.progress_callback.emit(("Generating RT Struct", 55))
                self.create_new_rtstruct(self.progress_callback)

        # Get isodose levels to turn into ROIs
        isodose_levels = \
            iso2roi.get_iso_levels('data/csv/batch_isodoseRoi.csv')

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Calculate boundaries
        self.progress_callback.emit(("Calculating boundaries...", 60))
        boundaries = iso2roi.calculate_isodose_boundaries(isodose_levels)

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            self.summary = "ISO_NO_RX_DOSE"
            return False

        # Generate ROIs
        self.progress_callback.emit(("Generating ROIs...", 80))
        iso2roi.generate_roi(boundaries, self.progress_callback)

        # Save new RTSS
        self.progress_callback.emit(("Saving RT Struct...", 90))
        self.save_rtss()
        return True
