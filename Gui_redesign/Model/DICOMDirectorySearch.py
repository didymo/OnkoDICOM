import os

from PyQt5.QtCore import QRunnable, pyqtSignal, pyqtSlot
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from Gui_redesign.Model.DICOMStructure import DICOMStructure, Patient, Study, Series, Image


def get_dicom_structure(path):
    """
    Searches the given directory and creates a Patient>Study>Series>Image structure based on the DICOM files in the
    directory and subdirectories.

    :param path: The root directory to search from.
    :return: Complete DICOMStructure object with associated DICOM files
    """

    dicom_structure = DICOMStructure()

    for root, dirs, files in os.walk(path):
        for file in files:

            # Fix to program crashing when encountering DICOMDIR files
            if file == "DICOMDIR":
                continue

            file_path = root + os.sep + file
            try:
                dicom_file = dcmread(file_path)
            except InvalidDicomError:
                pass
            else:
                new_image = Image(dicom_file, file_path)
                if not dicom_structure.has_patient(dicom_file.PatientID):
                    # TODO there is definitely a more efficient way of doing this
                    new_series = Series(dicom_file.SeriesInstanceUID)
                    new_series.add_image(new_image)

                    new_study = Study(dicom_file.StudyInstanceUID)
                    new_study.add_series(new_series)

                    new_patient = Patient(dicom_file.PatientID)
                    new_patient.add_study(new_study)

                    dicom_structure.add_patient(new_patient)
                else:
                    existing_patient = dicom_structure.get_patient(dicom_file.PatientID)
                    if not existing_patient.has_study(dicom_file.StudyInstanceUID):
                        new_series = Series(dicom_file.SeriesInstanceUID)
                        new_series.add_image(new_image)

                        new_study = Study(dicom_file.StudyInstanceUID)
                        new_study.add_series(new_series)

                        existing_patient.add_study(new_study)
                    else:
                        existing_study = existing_patient.get_study(dicom_file.StudyInstanceUID)
                        if not existing_study.has_series(dicom_file.SeriesInstanceUID):
                            new_series = Series(dicom_file.SeriesInstanceUID)
                            new_series.add_image(new_image)

                            existing_study.add_series(new_series)
                        else:
                            existing_series = existing_study.get_series(dicom_file.SeriesInstanceUID)
                            if not existing_series.has_image(dicom_file.SOPInstanceUID):
                                existing_series.add_image(new_image)

    return dicom_structure


if __name__ == "__main__":
    ds = get_dicom_structure("XR.Identified")
    print(ds.get_files())
