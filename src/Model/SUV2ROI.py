import numpy
from skimage import measure
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.InputDialogs import PatientWeightDialog


class SUV2ROI:
    """
    This class is for converting SUV levels to ROIs.
    """
    def __init__(self):
        self.patient_weight = None
        self.weight_over_dose = None
        self.suv2roi_status = False
        self.failure_reason = None

    def start_conversion(self, interrupt_flag, progress_callback):
        """
        Goes the the steps of the SUV2ROI conversion.
        :param interrupt_flag: interrupt flag to stop process.
        :param progress_callback: signal that receives the current
                                  progress of the process.
        :return: False if unsuccessful, True if successful.
        """
        # Get PET datasets
        progress_callback.emit(("Getting PET Data", 20))
        selected_files = self.find_PET_datasets()

        # Stop loading
        if interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            return False

        # Calculate contours
        progress_callback.emit(("Calculating Boundaries", 40))
        contour_data = self.calculate_contours()

        # Stop loading
        if interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            return False

        if not contour_data:
            # TODO: convert print to logging
            print("Boundaries could not be calculated.")
            return False

        # Generate ROIs
        progress_callback.emit(("Generating ROIs", 60))
        self.generate_ROI(contour_data, progress_callback)
        progress_callback.emit(("Reloading Window. Please Wait...", 95))
        self.suv2roi_status = True

    def find_PET_datasets(self):
        """
        Function to find datasets of PET files in currently open DICOM
        image dataset.
        :return: Dictionary where key is PET Image type (NAC or CTAC)
                 and value is a list of PET datasets of that type.
        """
        dicom_files = {"PT CTAC": [], "PT NAC": []}

        patient_dict_container = PatientDictContainer()
        dataset = patient_dict_container.dataset

        for ds in dataset:
            if dataset[ds].SOPClassUID == "1.2.840.10008.5.1.4.1.1.128":
                if 'CorrectedImage' in dataset[ds]:
                    if "ATTN" in dataset[ds].CorrectedImage:
                        dicom_files["PT CTAC"].append(dataset[ds])
                    else:
                        dicom_files["PT NAC"].append(dataset[ds])

        return dicom_files

    def get_patient_weight(self, dataset):
        """
        Attempts to set the patient weight from the dataset, then from
        the user. Sets the class' patient_weight variable with the
        patient's weight in grams.
        :param dataset: a DICOM PET dataset.
        """
        # Try get patient weight from dataset. An AttributeError will be
        # raised if the dataset does not contain patient weight
        try:
            self.patient_weight = dataset.PatientWeight * 1000
            return
        except AttributeError:
            # Since weight is not present, keep prompting the user for
            # it until they enter a valid number or close the dialog box
            dialog = PatientWeightDialog()
            if dialog.exec_():
                self.patient_weight = dialog.get_input() * 1000
                return
            else:
                self.patient_weight = None
                return

    def set_patient_weight(self, weight_in_grams):
        """
        Sets the patient weight to the value specified by the parameter.
        Used for batch processing.
        """
        self.patient_weight = weight_in_grams

    def pet2suv(self, dataset):
        """
        Converts DICOM PET pixel array values to SUV values. Currently
        only handles PET datasets in Bq/mL that are attenuation and
        decay corrected.
        :param dataset: the DICOM PET dataset.
        :return: DICOM PET pixel data in SUV.
        """
        # Return if units are not Bq/mL
        if not dataset.Units == "BQML":
            self.failure_reason = "UNIT"
            return None

        # Return if CorrectedImage does not contain DECY, and
        # decay correction is not START
        if (["DECY"] not in dataset.CorrectedImage) and \
                (dataset.DecayCorrection != "START"):
            self.failure_reason = "DECY"
            return None

        # Return if patient weight not set
        if self.patient_weight is None:
            self.failure_reason = "WEIGHT"
            return None

        # Get radiopharmaceutical information
        radiopharmaceutical_info = \
            dataset.RadiopharmaceuticalInformationSequence[0]

        # Calculate patient weight divided by total dose once
        if self.weight_over_dose is None:
            radionuclide_total_dose = \
                radiopharmaceutical_info['RadionuclideTotalDose'].value
            self.weight_over_dose = \
                self.patient_weight / radionuclide_total_dose

        # Get rescale slope and intercept
        rescale_slope = dataset.RescaleSlope
        rescale_intercept = dataset.RescaleIntercept

        # Get pixel data
        pixel_array = dataset.pixel_array

        # Convert Bq/ml to SUV
        suv = (pixel_array * rescale_slope + rescale_intercept) \
            * self.weight_over_dose

        # Return SUV data
        return suv

    def calculate_contours(self):
        """
        Calculate SUV boundaries for each slice from an SUV value of 1
        all the way to the maximum SUV value in that slice.
        :return: Dictionary where key is SUV ROI name and value is
                 a list containing tuples of slice id and lists of
                 contours.
        """
        # Create dictionary to store contour data
        contour_data = {}

        # Initialise variables needed for function
        patient_dict_container = PatientDictContainer()
        slider_min = 0
        slider_max = len(patient_dict_container.get("pixmaps_axial"))

        # Loop through each PET image in the dataset
        for slider_id in range(slider_min, slider_max):
            # Get SUV data from PET file
            temp_ds = patient_dict_container.dataset[slider_id]
            suv_data = self.pet2suv(temp_ds)

            # Return None if PET 2 SUV failed
            if suv_data is None:
                return None

            # Set current and max SUV for the current slice
            current_suv = 1
            max_suv = numpy.amax(suv_data)

            # Continue calculating SUV contours for the slice until the
            # max SUV has been reached.
            while current_suv < max_suv:
                # Find the contours for the SUV (i)
                contours = measure.find_contours(suv_data, current_suv)

                # Get the SUV name
                name = "SUV-" + str(current_suv)
                if name not in contour_data:
                    contour_data[name] = []
                contour_data[name].append((slider_id, contours))
                current_suv += 1

        # Return contour data
        return contour_data

    def generate_ROI(self, contours, progress_callback):
        """
        Generates new ROIs based on contour data.
        :param contours: dictionary of contours to turn into ROIs.
        :param progress_callback: signal that receives the current
                                  progress of the loading.
        """
        # Initialise variables needed for function
        patient_dict_container = PatientDictContainer()
        dataset_rtss = patient_dict_container.get("dataset_rtss")

        # Get existing ROIs
        existing_rois = []
        rois = patient_dict_container.get("dataset_rtss")
        if rois:
            for roi in rois.StructureSetROISequence:
                existing_rois.append(roi.ROIName)

        # Loop through each SUV level
        item_count = len(contours)
        current_progress = 60
        progress_increment = round((95 - 60)/item_count)
        for item in contours:
            # Delete ROI if it already exists to recreate it
            if item in existing_rois:
                dataset_rtss = ROI.delete_roi(dataset_rtss, item)

                # Update patient dict container
                current_rois = patient_dict_container.get("rois")
                keys = []
                for key, value in current_rois.items():
                    if value["name"] == item:
                        keys.append(key)
                for key in keys:
                    del current_rois[key]
                patient_dict_container.set("rois", current_rois)

            progress_callback.emit(("Generating ROIs", current_progress))
            current_progress += progress_increment

            # Loop through each slice
            for i in range(len(contours[item])):
                slider_id = contours[item][i][0]
                dataset = patient_dict_container.dataset[slider_id]
                pixlut = patient_dict_container.get("pixluts")
                pixlut = pixlut[dataset.SOPInstanceUID]
                z_coord = dataset.SliceLocation

                # List storing lists that contain all points for a
                # contour.
                single_array = []

                # Loop through each contour
                for j in range(len(contours[item][i][1])):
                    single_array.append([])
                    # Loop through every point in the contour
                    for point in contours[item][i][1][j]:
                        # Convert pixel coordinates to RCS points
                        rcs_pixels = ROI.pixel_to_rcs(pixlut, round(point[1]),
                                                      round(point[0]))
                        # Append RCS points to the single array
                        single_array[j].append(rcs_pixels[0])
                        single_array[j].append(rcs_pixels[1])
                        single_array[j].append(z_coord)

                # Create the ROI(s)
                for array in single_array:
                    rtss = ROI.create_roi(dataset_rtss, item,
                                          [{'coords': array, 'ds': dataset}],
                                          "")

                    # Save the updated rtss
                    patient_dict_container.set("dataset_rtss", rtss)
                    patient_dict_container.set("rois",
                                               ImageLoading.get_roi_info(rtss))
