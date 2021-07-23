# NOTE:
# This script assumes the presence of DICOM PET Image Storage files
# in the folder /test/testdata/DICOM-PT-TEST. This data is currently not
# provided due to privacy concerns.

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

    # Walk through directory
    for root, dirs, files in os.walk(file_path, topdown=True):
        for name in files:
            # Attempt to open file as a DICOM file
            try:
                ds = dcmread(os.path.join(root, name))
                if ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.128":
                    if 'CorrectedImage' in ds:
                        if "ATTN" in ds.CorrectedImage:
                            dicom_files["PT CTAC"] = root
                        else:
                            dicom_files["PT NAC"] = root
                    break
            except (InvalidDicomError, FileNotFoundError):
                pass
    return dicom_files


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