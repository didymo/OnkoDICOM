import pydicom, platform, os.path, datetime
from pathlib import Path
from pydicom.dataset import FileDataset, FileMetaDataset
from skimage import measure
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox
from src.Controller.PathHandler import resource_path
from src.Model import ImageLoading
from src.Model import ROI
from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.GetPatientInfo import DicomTree


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)
    signal_save_confirmation = QtCore.Signal()

class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn
        self.signal_save_confirmation = self.worker_signals.signal_save_confirmation
        self.signal_save_confirmation.connect(self.save_confirmation)
        self.advised_save_rtss = False
        self.isodose_levels = {}

    def start_conversion(self, interrupt_flag, progress_callback):
        """
        Goes the the steps of the iso2roi conversion.
        :param interrupt_flag: interrupt flag to stop process
        :param progress_callback: signal that receives the current progress of the loading.
        """
        patient_dict_container = PatientDictContainer()

        progress_callback.emit(("Validating Datasets", 0))
        val = ImageLoading.is_dataset_dicom_rt(patient_dict_container.dataset)

        # Stop loading
        if interrupt_flag.is_set():
            print("Stopped ISO2ROI")
            return False

        if not val:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not patient_dict_container.get("file_rtss"):
                # Stop loading
                if interrupt_flag.is_set():
                    print("Stopped ISO2ROI")
                    return False

                # Get common directory
                file_path = patient_dict_container.filepaths.values()
                file_path = Path(os.path.commonpath(file_path))

                progress_callback.emit(("Generating RT Structure Set", 30))
                # Create RT Struct file
                ds = self.generate_rtss(file_path)

                # Get new RT Struct file path
                file_path = str(file_path.joinpath("rtss.dcm"))

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
                patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

                patient_dict_container.set("selected_rois", [])
                patient_dict_container.set("dict_polygons_axial", {})

        # Get isodose levels to turn into ROIs
        self.get_iso_levels()

        # Stop loading
        if interrupt_flag.is_set():
            print("Stopped ISO2ROI")
            return False

        # Calculate dose boundaries
        progress_callback.emit(("Calculating Boundaries", 50))
        boundaries = self.calculate_boundaries()

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        # Stop loading
        if interrupt_flag.is_set():
            print("Stopped ISO2ROI")
            return False

        progress_callback.emit(("Generating ROIs", 75))
        self.generate_roi(boundaries, progress_callback)
        progress_callback.emit(("Reloading Window. Please Wait...", 95))

    def get_iso_levels(self):
        """
        Opens /data/csv/isodoseRoi.csv to find the isodose levels that
        the user wants turned into ROIs. Creates a dictionary where the
        key is the isoname, and the value is a list containing a boolean
        (cGy: 0, %: 1) and an integer (cGy/% value).
        """

        # Clear self.isodose_levels (in case ISO2ROI has already been
        # run this session)
        self.isodose_levels = {}

        # Open isodoseRoi.csv
        with open('data/csv/isodoseRoi.csv', "r") as fileInput:
            for row in fileInput:
                items = row.split(',')
                self.isodose_levels[items[2]] = [items[1] == 'cGy',
                                                 int(items[0])]

    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: coutours, a list containing the countours for each
                 isodose level.
        """
        # Initialise variables needed to find isodose levels
        patient_dict_container = PatientDictContainer()
        pixmaps = patient_dict_container.get("pixmaps_axial")
        slider_min = 0
        slider_max = len(pixmaps)

        rt_plan_dose = patient_dict_container.dataset['rtdose']
        rt_dose_dose = patient_dict_container.get("rx_dose_in_cgray")

        # If rt_dose_dose does not exist, return None
        if not rt_dose_dose:
            return None

        contours = {}

        for item in self.isodose_levels:
            # Calculate boundaries for each isodose level for each slice
            contours[item] = []
            for slider_id in range(slider_min, slider_max):
                contours[item].append([])
                z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
                grid = get_dose_grid(rt_plan_dose, float(z))

                if not (grid == []):
                    if self.isodose_levels[item][0]:
                        dose_level = self.isodose_levels[item][1] / \
                                     (rt_plan_dose.DoseGridScaling * 100)
                        contours[item][slider_id] =\
                            (measure.find_contours(grid, dose_level))
                    else:
                        dose_level = self.isodose_levels[item][1] * \
                                     rt_dose_dose / \
                                     (rt_plan_dose.DoseGridScaling * 10000)
                        contours[item][slider_id] = \
                            (measure.find_contours(grid, dose_level))

        # Return list of contours for each isodose level for each slice
        return contours

    def generate_roi(self, contours, progress_callback):
        """
        Generates new ROIs based on contour data.
        :param contours: dictionary of contours to turn into ROIs.
        """
        # Initialise variables needed for function
        patient_dict_container = PatientDictContainer()
        dataset_rtss = patient_dict_container.get("dataset_rtss")
        pixmaps = patient_dict_container.get("pixmaps_axial")
        slider_min = 0
        slider_max = len(pixmaps) - 1

        # Save RTSS if it has been modified but not saved
        if patient_dict_container.get("rtss_modified"):
            rtss_directory = Path(patient_dict_container.get("file_rtss"))
            patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
            patient_dict_container.set("rtss_modified", False)

        # Calculate isodose ROI for each slice, skip if slice has no
        # contour data
        for item in contours:
            for i in range(slider_min, slider_max):
                if not len(contours[item][i]):
                    continue

                # Get required data for calculating ROI
                dataset = patient_dict_container.dataset[i]
                pixlut = patient_dict_container.get("pixluts")[dataset.SOPInstanceUID]
                z_coord = dataset.SliceLocation
                curr_slice_uid = patient_dict_container.get("dict_uid")[i]
                dose_pixluts = patient_dict_container.get("dose_pixluts")[curr_slice_uid]

                # Loop through each contour for each slice.
                # Convert the pixel points to RCS points, append z value
                single_array = []

                # Loop through each contour
                for j in range(len(contours[item][i])):
                    single_array.append([])
                    # Loop through each point in the contour
                    for point in contours[item][i][j]:
                        # Transform into dose pixel
                        dose_pixels = [dose_pixluts[0][int(point[1])],
                                       dose_pixluts[1][int(point[0])]]
                        # Transform into RCS pixel
                        rcs_pixels = ROI.pixel_to_rcs(pixlut,
                                                      round(dose_pixels[0]),
                                                      round(dose_pixels[1]))
                        # Append point coordinates to the single array
                        single_array[j].append(rcs_pixels[0])
                        single_array[j].append(rcs_pixels[1])
                        single_array[j].append(z_coord)

                # Create the ROI(s)
                for array in single_array:
                    rtss = ROI.create_roi(dataset_rtss, item,
                                          array, dataset, "DOSE_REGION")

                    # Save the updated rtss
                    patient_dict_container.set("dataset_rtss", rtss)
                    patient_dict_container.set("rois",
                                               ImageLoading.get_roi_info(rtss))

        self.advised_save_rtss = False

        progress_callback.emit(("Writing to RT Structure Set", 85))

        # Get confirmation from user, save rtss if user selects so
        self.worker_signals.signal_save_confirmation.emit()

        # Do not continue until selection is made by user
        while not self.advised_save_rtss:
            continue

    def save_confirmation(self):
        """Saves the new ROIs to rtss."""
        patient_dict_container = PatientDictContainer()
        rtss_directory = Path(patient_dict_container.get("file_rtss"))
        patient_dict_container.get("dataset_rtss").save_as(rtss_directory)
        patient_dict_container.set("rtss_modified", False)

        # Allow the program to continue running
        self.advised_save_rtss = True

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
        rtss.PatientSex = patient_dict_container.dataset[0].PatientSex

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
