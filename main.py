# NOTE:
# This script assumes the presence of DICOM PET Image Storage files
# in the folder /test/testdata/DICOM-PT-TEST. This data is currently not
# provided due to privacy concerns.
import numpy
from PIL import Image
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

import os
import platform


def find_DICOM_files(file_path):
    """
    Function to find directories of DICOM PET Image files in a given
    folder.
    :param file_path: File path of folder to search.
    :return: Dictionary where key is PET Image type (NAC or CTAC) and
             value is directory where PET Image files of that type are.
    """

    dicom_files = {}
    dicom_files["PT CTAC"] = []
    dicom_files["PT NAC"] = []

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


def get_SUV_data(selected_files):
    """
    Gets SUV pixel data from the files in the selected_files dictionary.
    :param selected_files: A dictionary of files to get SUV pixel data
                           from.
    :return: Dictionary of file names and SUV pixel data.
    """
    suv_data = {}

    # Loop through each file
    for key in selected_files:
        suv_data[key] = []
        for i in range(0, len(selected_files[key])):
            file_path = selected_files[key][i]
            # Read the file
            ds = dcmread(file_path)
            suv = pet2suv(ds)
            suv_data[key].append(suv)
            #img2d = suv.astype(float)
            #img2d_scaled = (numpy.maximum(img2d, 0) / img2d.max()) * 255.0
            #img2d_scaled = 255 - img2d_scaled
            #img2d_scaled = numpy.uint8(img2d_scaled)
            #img = Image.fromarray(img2d_scaled)
            #img.show()

    return suv_data

def pet2suv(dataset):
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
    decay = numpy.exp(numpy.log(2) *
                      (series_time_s - radiopharmaceutical_start_time_s)
                      / radionuclide_half_life)
    suv = (pixel_array * rescale_slope + rescale_intercept) * decay
    #suv = pixel_array * decay
    suv = suv * (1000 * patient_weight) / radionuclide_total_dose
    return suv

if __name__ == '__main__':
    # Load test DICOM files
    if platform.system() == "Windows":
        desired_path = "\\test\\testdata\\DICOM-PT-TEST"
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        desired_path = "/test/testdata/DICOM-PT-TEST"

    desired_path = os.path.dirname(os.path.realpath(__file__)) + desired_path

    # list of DICOM test files
    selected_files = find_DICOM_files(desired_path)
    if "PT CTAC" in selected_files:
        if "PT NAC" in selected_files:
            print("CTAC and NAC data in DICOM Image Set")
        else:
            print("CTAC data in DICOM Image Set")
    elif "PT NAC" in selected_files:
        print("NAC data in DICOM Image Set")
    else:
        print("No PET data in DICOM Image Set")

    get_SUV_data(selected_files)