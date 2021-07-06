from pydicom import dcmread
from pydicom.errors import InvalidDicomError

import os.path
import platform


class CheckAttributes:
    def __init__(self, file_path):
        self.file_path = file_path
        self.files = []
        self.DICOM_files = {}

    def find_DICOM_files(self):
        """
        Find all DICOM files in the default directory.
        """
        total_files = sum([len(files) for root, dirs, files in os.walk(self.file_path)])
        if total_files:
            for root, dirs, files in os.walk(self.file_path, topdown=True):
                for name in files:
                    file_name = os.path.join(root, name)
                    try:
                        dicom_file = dcmread(file_name)
                    except (InvalidDicomError, FileNotFoundError):
                        pass
                    else:
                        self.DICOM_files[file_name] = dicom_file

        print("\nFound %s DICOM files." % len(self.DICOM_files))

    def get_DICOM_files(self):
        """
        Returns the list of DICOM files.
        :return: Dictionary of DICOM files found in self.file_path
        """
        return self.DICOM_files

    def get_type(self, DICOM_file):
        """
        Returns the type of data contained within a DICOM file
        :return: string type of data in DICOM file
        """
        elements = {
            '1.2.840.10008.5.1.4.1.1.481.3': "RT Struct",
            '1.2.840.10008.5.1.4.1.1.2': "CT Image",
            '1.2.840.10008.5.1.4.1.1.481.2': "RT Dose",
            '1.2.840.10008.5.1.4.1.1.481.5': "RT Plan"
        }

        class_uid = DICOM_file["SOPClassUID"].value
        # Check to see what type of data the given DICOM file holds
        if class_uid in elements:
            return elements[class_uid]
        else:
            return "---"

    def check_elements(self):
        """
        Checks to see if the DICOM files have certain elements, returning a dictionary of elements and if they exist
        in the DICOM-RT image set.
        :return: elements_present, a dictionary with elements as the key (string) and their presence as the value (bool)
        """
        # Return if there are no DICOM files
        if len(self.DICOM_files) == 0:
            print("Error: no DICOM files.")
            return

        # List of elements we are looking for (SOP Class UIDs and their meanings)
        elements = {
            '1.2.840.10008.5.1.4.1.1.481.3': "RT Struct",
            '1.2.840.10008.5.1.4.1.1.2': "CT Image",
            '1.2.840.10008.5.1.4.1.1.481.2': "RT Dose",
            '1.2.840.10008.5.1.4.1.1.481.5': "RT Plan"
        }

        # Dictionary of present elements
        elements_present = {
            "RT Struct": False, "CT Image": False,
            "RT Dose": False, "RT Plan": False
        }

        # Check each DICOM file to see what it contains
        for dicom_file in self.DICOM_files:
            class_uid = self.DICOM_files[dicom_file]["SOPClassUID"].value
            # Check to see if element is of interest and that we haven't already found it in the DICOM file set
            if class_uid in elements:
                if not elements_present[elements[class_uid]]:
                    elements_present[elements[class_uid]] = True

        # Return elements present in DICOM-RT image set
        return elements_present


if __name__ == "__main__":
    # Load test DICOM files
    if platform.system() == "Windows":
        file_path = "\\test\\testdata\\DICOM-RT-TEST"
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        file_path = "/test/testdata/DICOM-RT-TEST"

    # Get the absolute file path
    file_path = os.path.dirname(os.path.realpath(__file__)) + file_path

    # Create a CheckAttributes object
    check_attributes = CheckAttributes(file_path)

    # Find all DICOM files in file_path and its sub-directories and return the presence of certain elements
    check_attributes.find_DICOM_files()
    present_elements = check_attributes.check_elements()

    # Check to make sure that CT and RTDOSE data is present
    if present_elements["CT Image"] and present_elements["RT Dose"]:
        print("CT and RTDOSE data present in DICOM-RT image set located in %s" % file_path)
    elif present_elements["CT Image"] and not present_elements["RT Dose"]:
        print("CT data present in DICOM-RT image set located in %s" % file_path)
    elif not present_elements["CT Image"] and present_elements["RT Dose"]:
        print("RTDOSE data present in DICOM-RT image set located in %s" % file_path)
    else:
        print("CT and RTDOSE data not present in DICOM-RT image set located in %s" % file_path)