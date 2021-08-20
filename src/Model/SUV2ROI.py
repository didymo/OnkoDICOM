from pathlib import Path
from pydicom.dataset import FileDataset, FileMetaDataset
from PySide6 import QtCore, QtWidgets
from skimage import measure
from skimage.transform import resize
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.PatientDictContainer import PatientDictContainer

import datetime
import pydicom


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)


class SUV2ROI:
    """This class is for converting SUV levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn

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

    def pet2suv(self, dataset):
        """
        Converts DICOM PET pixel array values (which are in Bq/ml) to
        SUV values.
        :param dataset: the DICOM PET dataset.
        :return: DICOM PET pixel data in SUV.
        """
        # Get series and acquisition time
        series_time = dataset.SeriesTime
        #acquisition_time = dataset.AcquisitionTime

        # Get patient info
        #patient_weight = dataset.PatientWeight
        patient_weight = 87

        # Get radiopharmaceutical information
        radiopharmaceutical_info = \
            dataset.RadiopharmaceuticalInformationSequence[0]
        radiopharmaceutical_start_time = \
            radiopharmaceutical_info['RadiopharmaceuticalStartTime'].value
        radionuclide_total_dose = \
            radiopharmaceutical_info['RadionuclideTotalDose'].value
        #radionuclide_half_life = \
        #    radiopharmaceutical_info['RadionuclideHalfLife'].value

        # Get rescale slope and intercept
        rescale_slope = dataset.RescaleSlope
        rescale_intercept = dataset.RescaleIntercept

        # Convert series and acquisition time to seconds
        #series_time_s = (float(series_time[0:2]) * 3600) +\
        #                (float(series_time[2:4]) * 60) +\
        #                float(series_time[4:6])
        #radiopharmaceutical_start_time_s =\
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
        suv = (pixel_array * rescale_slope + rescale_intercept) * decay
        suv = suv * (1000 * patient_weight) / radionuclide_total_dose

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
        contour_data = {}

        patient_dict_container = PatientDictContainer()
        slider_min = 0
        slider_max = len(patient_dict_container.get("pixmaps_axial"))

        for slider_id in range(slider_min, slider_max):
            temp_ds = patient_dict_container.dataset[slider_id]

            i = 1

            while True:
                suv_data = self.pet2suv(temp_ds)
                contours = measure.find_contours(suv_data, i)
                if not contours:
                    break
                else:
                    name = "SUV-" + str(i)
                    if name not in contour_data:
                        contour_data[name] = []
                    contour_data[name].append((slider_id, contours))
                    i += 1

        return contour_data

    def generate_ROI(self, contours):
        """
        Generates new ROIs based on contour data.
        :param contours: dictionary of contours to turn into ROIs
        """
        # Initialise variables needed for function
        patient_dict_container = PatientDictContainer()
        dataset_rtss = patient_dict_container.get("dataset_rtss")

        # Loop through each SUV level
        for item in contours:
            print("\n==Generating ROIs for " + str(item) + "==")
            # Loop through each slice
            for i in range(len(contours[item])):
                slider_id = contours[item][i][0]
                dataset = patient_dict_container.dataset[slider_id]
                pixlut = patient_dict_container.get("pixluts")
                pixlut = pixlut[dataset.SOPInstanceUID]
                z_coord = dataset.SliceLocation

                # Convert pixel coordinates to RCS points
                points = []
                for j in range(len(contours[item][i][1])):
                    points.append([])
                    for point in contours[item][i][1][j]:
                        points[j].append(ROI.pixel_to_rcs(pixlut,
                                                          round(point[1]),
                                                          round(point[0])))

                # Append Z coordinate
                contour_data = []
                for i in range(len(points)):
                    contour_data.append([])
                    for p in points[i]:
                        coords = (p[0], p[1], z_coord)
                        contour_data[i].append(coords)

                # Transform RCS points into 1D array
                single_array = []
                for i in range(len(contour_data)):
                    single_array.append([])
                    for sublist in contour_data[i]:
                        for point in sublist:
                            single_array[i].append(point)

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

        # Save the new ROIs to the RT Struct file
        rtss_directory = Path(patient_dict_container.get("file_rtss"))

        message = "Are you sure you want to save the modified RTSTRUCT file? "
        message += "This will overwrite the existing file. "
        message += "This is not reversible."
        confirm_save = QtWidgets.QMessageBox.information(None, "Confirmation",
                                                         message,
                                                         QtWidgets.QMessageBox.Yes,
                                                         QtWidgets.QMessageBox.No)

        if confirm_save == QtWidgets.QMessageBox.Yes:
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            QtWidgets.QMessageBox.about(None, "File saved",
                                        "The RTSTRUCT file has been saved.")
            patient_dict_container.set("rtss_modified", False)

    def generate_rtss(self, file_path):
        """
        Creates an RT Struct file in the DICOM dataset directory if one
        currently does not exist. All required tags will be present
        making the file valid, however these tags will be blank.
        :param file_path: directory where DICOM dataset is stored.
        :return: ds, the newly created dataset.
        """
        # Define file name of rtss
        file_name = file_path.joinpath("rtss.dcm")

        # Define time and date
        time_now = datetime.datetime.now()

        # Create file meta dataset
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
        file_meta.MediaStorageSOPInstanceUID = '1.2.3'
        file_meta.ImplementationClassUID = '1.2.3.4'

        # Create RTSS
        rtss = FileDataset(file_name, {}, b"\0" * 128, file_meta)

        # Get Study Instance UID from another file in the dataset
        patient_dict_container = PatientDictContainer()

        # Add required data elements
        # Patient information
        rtss.PatientName = patient_dict_container.dataset[0].PatientName
        rtss.PatientID = patient_dict_container.dataset[0].PatientID
        rtss.PatientBirthDate = patient_dict_container.dataset[0].PatientBirthDate

        # General study information
        rtss.StudyDate = time_now.strftime('%Y%m%d')
        rtss.StudyTime = time_now.strftime('%H%M%S.%f')
        rtss.AccessionNumber = ''
        rtss.ReferringPhysicianName = ''
        rtss.StudyInstanceUID = patient_dict_container.dataset[0].StudyInstanceUID
        rtss.StudyID = ''

        # RT series information
        rtss.Modality = 'RTSTRUCT'
        rtss.OperatorsName = ''
        rtss.SeriesInstanceUID = '1.2.3.4'  # MUST be unique, currently not
        rtss.SeriesNumber = ''

        # General equipment information
        rtss.Manufacturer = ''

        # Structure set information
        rtss.StructureSetLabel = ''
        rtss.StructureSetDate = ''
        rtss.StructureSetTime = ''
        rtss.StructureSetROISequence = ''

        # ROI contour information
        rtss.ROIContourSequence = ''

        # RT ROI observations information
        rtss.RTROIObservationsSequence = ''

        # SOP common information
        rtss.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
        rtss.SOPInstanceUID = '1.2.3.4'  # MUST be unique, currently not

        # Write file
        rtss.save_as(file_name)

        # Read back in dataset
        ds = pydicom.dcmread(file_name)

        # Set patient dict container values
        # Set pixluts
        dict_pixluts = ImageLoading.get_pixluts(patient_dict_container.dataset)
        patient_dict_container.set("pixluts", dict_pixluts)

        # Set ROIs
        rois = ImageLoading.get_roi_info(ds)
        patient_dict_container.set("rois", rois)

        # Return new dataset
        return ds
