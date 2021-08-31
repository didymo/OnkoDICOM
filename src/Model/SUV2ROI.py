import numpy
import os
from pathlib import Path
from PySide6 import QtCore
from skimage import measure
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.GetPatientInfo import DicomTree
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.InputDialogs import PatientWeightDialog


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)


class SUV2ROI:
    """This class is for converting SUV levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn

        self.patient_weight = None
        self.weight_over_dose = None

    def start_conversion(self, interrupt_flag, progress_callback):
        """
        Goes the the steps of the SUV2ROI conversion.
        :param interrupt_flag: interrupt flag to stop process.
        :param progress_callback: signal that receives the current
                                  progress of the process.
        """
        patient_dict_container = PatientDictContainer()

        progress_callback.emit(("Validating Datasets", 0))
        dataset_complete = \
            ImageLoading.is_dataset_dicom_rt(patient_dict_container.dataset)

        # Stop loading
        if interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            return False

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not patient_dict_container.get("file_rtss"):
                # Stop loading
                if interrupt_flag.is_set():
                    # TODO: convert print to logging
                    print("Stopped SUV2ROI")
                    return False
                progress_callback.emit(("Creating RT Struct", 20))
                self.create_new_rtstruct()

        # Get PET datasets
        progress_callback.emit(("Getting PET Data", 40))
        selected_files = self.find_PET_datasets()

        # Stop loading
        if interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped SUV2ROI")
            return False

        if "PT CTAC" in selected_files:
            if "PT NAC" in selected_files:
                print("CTAC and NAC data in DICOM Image Set")
            else:
                print("CTAC data in DICOM Image Set")
        elif "PT NAC" in selected_files:
            print("NAC data in DICOM Image Set")
        else:
            print("No PET data in DICOM Image Set")

        # Calculate contours
        progress_callback.emit(("Calculating Boundaries", 50))
        contour_data = self.calculate_contours()

        # Stop loading
        if interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ISO2ROI")
            return False

        if not contour_data:
            # TODO: convert print to logging
            print("Boundaries could not be calculated.")
            return

        # Generate ROIs
        progress_callback.emit(("Generating ROIs", 60))
        self.generate_ROI(contour_data, progress_callback)
        progress_callback.emit(("Reloading Window. Please Wait...", 95))

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
                print("Patient weight not entered. Stopping!")
                self.patient_weight = None
                return

    def pet2suv(self, dataset):
        """
        Converts DICOM PET pixel array values (which are in Bq/ml) to
        SUV values.
        :param dataset: the DICOM PET dataset.
        :return: DICOM PET pixel data in SUV.
        """
        # Get series and acquisition time
        series_time = dataset.SeriesTime
        # acquisition_time = dataset.AcquisitionTime

        # Get radiopharmaceutical information
        radiopharmaceutical_info = \
            dataset.RadiopharmaceuticalInformationSequence[0]
        radiopharmaceutical_start_time = \
            radiopharmaceutical_info['RadiopharmaceuticalStartTime'].value

        # Calculate patient weight divided by total dose once
        if self.weight_over_dose is None:
            radionuclide_total_dose = \
                radiopharmaceutical_info['RadionuclideTotalDose'].value
            self.weight_over_dose = \
                self.patient_weight / radionuclide_total_dose

        # radionuclide_half_life = \
        #    radiopharmaceutical_info['RadionuclideHalfLife'].value

        # Get rescale slope and intercept
        rescale_slope = dataset.RescaleSlope
        rescale_intercept = dataset.RescaleIntercept

        # Convert series and acquisition time to seconds
        # series_time_s = (float(series_time[0:2]) * 3600) +\
        #                (float(series_time[2:4]) * 60) +\
        #                float(series_time[4:6])
        # radiopharmaceutical_start_time_s =\
        #    (float(radiopharmaceutical_start_time[0:2]) * 3600) +\
        #    (float(radiopharmaceutical_start_time[2:4]) * 60) +\
        #    float(radiopharmaceutical_start_time[4:6])

        # Get pixel data
        pixel_array = dataset.pixel_array

        # Calculate decay
        # do not need to take decay into account if DECY in CorrectedImage
        # decay = numpy.exp(numpy.log(2) *
        #                  (series_time_s - radiopharmaceutical_start_time_s)
        #                  / radionuclide_half_life)
        decay = 1

        # Convert Bq/ml to SUV
        suv = (pixel_array * rescale_slope + rescale_intercept) * decay * \
            self.weight_over_dose

        # Return SUV data
        return suv

    def calculate_contours(self):
        """
        Calculate SUV boundaries for each slice from an SUV value of 3
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

            # Return if patient weight does not exist
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

        # Save RTSS if it has been modified but not saved
        if patient_dict_container.get("rtss_modified"):
            rtss_directory = Path(patient_dict_container.get("file_rtss"))
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            patient_dict_container.set("rtss_modified", False)

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

            print("\n==Generating ROIs for " + str(item) + "==")
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
                print("Generating ROI for slice " + str(slider_id))
                for array in single_array:
                    # TODO: change "DOSE_REGION"!!
                    rtss = ROI.create_roi(dataset_rtss, item,
                                          array, dataset, "DOSE_REGION")

                    # Save the updated rtss
                    patient_dict_container.set("dataset_rtss", rtss)
                    patient_dict_container.set("rois",
                                               ImageLoading.get_roi_info(rtss))

        progress_callback.emit(("Writing to RT Structure Set", 85))
        rtss_directory = Path(patient_dict_container.get("file_rtss"))
        patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
        patient_dict_container.set("rtss_modified", False)

    def create_new_rtstruct(self):
        """
        Generates a new RTSS and edits the patient dict container.
        """
        # Get common directory
        patient_dict_container = PatientDictContainer()
        file_path = patient_dict_container.filepaths.values()
        file_path = Path(os.path.commonpath(file_path))

        # Get new RT Struct file path
        file_path = str(file_path.joinpath("rtss.dcm"))

        # Create RT Struct file
        ct_uid_list = ImageLoading.get_image_uid_list(
            patient_dict_container.dataset)
        ds = ROI.create_initial_rtss_from_ct(
            patient_dict_container.dataset[0], file_path, ct_uid_list)
        ds.save_as(file_path)

        # Add RT Struct file path to patient dict container
        patient_dict_container.filepaths['rtss'] = file_path
        filepaths = patient_dict_container.filepaths

        # Add RT Struct dataset to patient dict container
        patient_dict_container.dataset['rtss'] = ds
        dataset = patient_dict_container.dataset

        # Set some patient dict container attributes
        patient_dict_container.set("file_rtss", filepaths['rtss'])
        patient_dict_container.set("dataset_rtss", dataset['rtss'])

        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss",
                                   dicom_tree_rtss.dict)

        dict_pixluts = ImageLoading.get_pixluts(
            patient_dict_container.dataset)
        patient_dict_container.set("pixluts", dict_pixluts)

        rois = ImageLoading.get_roi_info(ds)
        patient_dict_container.set("rois", rois)

        patient_dict_container.set("selected_rois", [])
        patient_dict_container.set("dict_polygons_axial", {})
