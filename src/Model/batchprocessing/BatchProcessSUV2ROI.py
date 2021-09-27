from src.Model import InitialModel
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.SUV2ROI import SUV2ROI
from src.Model.batchprocessing.BatchProcess import BatchProcess


class BatchProcessSUV2ROI(BatchProcess):
    """
    This class handles batch processing for the ISO2ROI process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for SUV2ROI
    allowed_classes = {
        # PET Image
        "1.2.840.10008.5.1.4.1.1.128": {
            "name": "pet",
            "sliceable": True
        },
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        }
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 patient_weight):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param patient_weight: Weight of the patient in grams.
        """
        # Call the parent class
        super(BatchProcessSUV2ROI, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['pet']
        self.ready = self.load_images(patient_files, self.required_classes)
        self.patient_weight = patient_weight

    def start(self):
        """
        Goes through the steps of the SUV2ROI conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
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
            print("Stopped SUV2ROI")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))
        dataset_complete = ImageLoading.is_dataset_dicom_rt(
            self.patient_dict_container.dataset)

        # Create SUV2ROI object
        suv2roi = SUV2ROI()
        suv2roi.set_patient_weight(self.patient_weight)
        self.progress_callback.emit(("Performing SUV2ROI... ", 50))

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
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

        # Calculate boundaries
        self.progress_callback.emit(("Calculating Boundaries", 60))
        contour_data = suv2roi.calculate_contours()

        if not contour_data:
            # TODO: convert print to logging
            print("Boundaries could not be calculated.")
            self.summary = "SUV_" + suv2roi.failure_reason
            return False

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            self.summary = "INTERRUPT"
            return False

        # Generate ROIs
        self.progress_callback.emit(("Generating ROIs...", 80))
        suv2roi.generate_ROI(contour_data, self.progress_callback)

        # Save new RTSS
        self.progress_callback.emit(("Saving RT Struct...", 90))
        self.save_rtss()
        return True
