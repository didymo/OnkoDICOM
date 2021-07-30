# NOTE:
# This script assumes the presence of DICOM PET Image Storage files
# in the folder /test/testdata/DICOM-PT-TEST. This data is currently not
# provided due to privacy concerns.
from PySide6 import QtCore, QtWidgets

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from skimage import measure
from skimage.transform import resize

import os
import platform


class WorkerSignals(QtCore.QObject):
    signal_roi_drawn = QtCore.Signal(tuple)


class SUV2ROI:
    """This class is for converting SUV levels to ROIs."""
    def __init__(self):
        self.worker_signals = WorkerSignals()
        self.signal_roi_drawn = self.worker_signals.signal_roi_drawn
        self.isodose_levels = {}

    def find_DICOM_files(self, file_path):
        """
        Function to find directories of DICOM PET Image files in a given
        folder.
        :param file_path: File path of folder to search.
        :return: Dictionary where key is PET Image type (NAC or CTAC) and
                 value is directory where PET Image files of that type are.
        """
        dicom_files = {"PT CTAC": [], "PT NAC": []}

        # Walk through directory
        for root, dirs, files in os.walk(file_path, topdown=True):
            for name in files:
                # Attempt to open file as a DICOM file
                try:
                    ds = dcmread(os.path.join(root, name))
                    if ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.128":
                        if 'CorrectedImage' in ds:
                            if "ATTN" in ds.CorrectedImage:
                                dicom_files["PT CTAC"].append(os.path.join(root, name))
                            else:
                                dicom_files["PT NAC"].append(os.path.join(root, name))
                except (InvalidDicomError, FileNotFoundError):
                    pass

        return dicom_files

    def get_SUV_data(self, selected_files):
        """
        Gets SUV pixel data from the files in the selected_files dictionary.
        :param selected_files: A dictionary of files to get SUV pixel data
                               from.
        :return: Dictionary of file names and SUV pixel data.
        """
        suv_data = []

        # Loop through each file
        for dicom_file in selected_files:
            file_path = dicom_file

            # Read the file
            ds = dcmread(file_path)
            suv = pet2suv(ds)
            # NOTE - SliceLocation is relative to an unspecified reference
            # point. A better Z for these slices would be in Image
            # Position (Patient), however the Z value here most likely does
            # not correspond to the Z value for the same (or closest) slice
            # in CT scans. Aligning these requires image fusion and is out
            # of the scope of this work.
            slice_location = float(ds['SliceLocation'].value)

            # Resize the SUV data to be 512x512 using nearest neighbour
            # scaling as it preserves SUV values at the expense of
            # accurate image scaling
            suv_data.append((slice_location, resize(suv, (512, 512), order=0)))

            # Temporary, for displaying SUV data
            #img2d = resize(suv, (512, 512)).astype(float)
            #img2d_scaled = (numpy.maximum(img2d, 0) / img2d.max()) * 255.0
            #img2d_scaled = 255 - img2d_scaled
            #img2d_scaled = numpy.uint8(img2d_scaled)
            #img = Image.fromarray(img2d_scaled)
            #img.show()

        # Sort the SUV data by Z value (-ve to +ve)
        suv_data.sort(key=lambda x: x[0])

        return suv_data

    def pet2suv(self, dataset):
        """
        Converts DICOM PET pixel array values (which are in Bq/ml) to SUV
        values.
        :param dataset: the DICOM PET dataset.
        :return: DICOM PET pixel data in SUV.
        """
        # Get series and acquisition time
        series_time = dataset.SeriesTime
        acquisition_time = dataset.AcquisitionTime

        # Get patient info
        patient_weight = dataset.PatientWeight

        # Get radiopharmaceutical information
        radiopharmaceutical_info = \
            dataset.RadiopharmaceuticalInformationSequence[0]
        radiopharmaceutical_start_time = \
            radiopharmaceutical_info['RadiopharmaceuticalStartTime'].value
        radionuclide_total_dose = \
            radiopharmaceutical_info['RadionuclideTotalDose'].value
        radionuclide_half_life = \
            radiopharmaceutical_info['RadionuclideHalfLife'].value

        # Get rescale slope and intercept
        rescale_slope = dataset.RescaleSlope
        rescale_intercept = dataset.RescaleIntercept

        # Convert series and acquisition time to seconds
        series_time_s = (float(series_time[0:2]) * 3600) +\
                        (float(series_time[2:4]) * 60) +\
                        float(series_time[4:6])
        radiopharmaceutical_start_time_s =\
            (float(radiopharmaceutical_start_time[0:2]) * 3600) +\
            (float(radiopharmaceutical_start_time[2:4]) * 60) +\
            float(radiopharmaceutical_start_time[4:6])

        # Calculate SUV
        pixel_array = dataset.pixel_array
        # do not need to take decay into account if DECY in CorrectedImage
        # decay = numpy.exp(numpy.log(2) *
        #                  (series_time_s - radiopharmaceutical_start_time_s)
        #                  / radionuclide_half_life)
        decay = 1
        # Need to scale PET units to get them into Bq/ml according to
        # http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.9.html
        suv = (pixel_array * rescale_slope + rescale_intercept) * decay
        # suv = pixel_array * decay
        suv = suv * (1000 * patient_weight) / radionuclide_total_dose
        return suv

    def calculate_contours(self, suv_data):
        """
        Calculate SUV boundaries for each slice from an SUV value of 3
        all the way to the maximum SUV value in that slice.
        :return: Dictionary where key is Z value of slice and value is
                 list of lists of contours.
        """
        contour_data = {}

        for i, slice in enumerate(suv_data):
            contour_data[slice[0]] = []
            for j in range(0, int(slice[1].max()) - 2):
                contour_data[slice[0]].append(measure.find_contours(slice[1], j + 3))

        return contour_data


if __name__ == '__main__':
    # Load test DICOM files
    if platform.system() == "Windows":
        desired_path = "\\test\\testdata\\DICOM-PT-TEST"
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        desired_path = "/test/testdata/DICOM-PT-TEST"

    desired_path = os.path.dirname(os.path.realpath(__file__)) + desired_path

    suv2roi = SUV2ROI()

    # list of DICOM test files
    print("Getting PET images")
    selected_files = suv2roi.find_DICOM_files(desired_path)
    if "PT CTAC" in selected_files:
        if "PT NAC" in selected_files:
            print("CTAC and NAC data in DICOM Image Set")
        else:
            print("CTAC data in DICOM Image Set")
    elif "PT NAC" in selected_files:
        print("NAC data in DICOM Image Set")
    else:
        print("No PET data in DICOM Image Set")

    # Use CTAC data if it exists and there is the same or more of it
    # than NAC data for further work, otherwise use NAC data
    if len(selected_files["PT CTAC"]) >= len(selected_files["PT NAC"]):
        data = selected_files["PT CTAC"]
    else:
        data = selected_files["PT NAC"]

    print("Calculating SUV data")
    suv_data = suv2roi.get_SUV_data(data)
    print("Calculating contours")
    contour_data = suv2roi.calculate_contours(suv_data)
    print("Generating ROIs")
    suv2roi.generate_ROI(contour_data)
    print("Done")

    # TODO: create ROI based on contour data
    #       - convert pixel data to RCS data (see ISO2ROI)
    #       - turn data into single array (see ISO2ROI)
    #       - create ROI from single array (will NOT currently match up
    #         with CT data, requires image fusion and transforms that
    #         another team is working on)
