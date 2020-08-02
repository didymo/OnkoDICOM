import os

from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from src.Model.DICOMStructure import DICOMStructure, Patient, Study, Series, Image


def get_dicom_structure(path, progress_callback):
    """
    Searches the given directory and creates a Patient>Study>Series>Image structure based on the DICOM files in the
    directory and subdirectories.

    :param path: The root directory to search from.
    :return: Complete DICOMStructure object with associated DICOM files
    """

    dicom_structure = DICOMStructure()

    files_searched = 0
    total_files = sum([len(files) for root, dirs, files in os.walk(path)])

    for root, dirs, files in os.walk(path):
        no_patient_id = 1
        for file in files:

            # The progress is updated first because the total files represents ALL files inside the selected directory,
            # not just the DICOM files. Otherwise, most files would be skipped and the progress would be inaccurate.
            files_searched += 1
            progress_callback.emit("%s/%s" % (files_searched, total_files))

            # Fix to program crashing when encountering DICOMDIR files
            if file == "DICOMDIR":
                continue

            file_path = root + os.sep + file
            try:
                dicom_file = dcmread(file_path)
            except (InvalidDicomError, FileNotFoundError):
                pass
            else:
                if 'PatientID' in dicom_file:
                    patient_id = dicom_file.PatientID
                else:
                    patient_id = "no_id_" + str(no_patient_id)
                    no_patient_id += 1

                new_image = Image(dicom_file, file_path)
                if not dicom_structure.has_patient(patient_id):
                    # TODO there is definitely a more efficient way of doing this
                    new_series = Series(dicom_file.SeriesInstanceUID)
                    new_series.series_description = dicom_file.get("SeriesDescription")
                    new_series.add_image(new_image)

                    new_study = Study(dicom_file.StudyInstanceUID)
                    new_study.study_description = dicom_file.get("StudyDescription")
                    new_study.add_series(new_series)

                    new_patient = Patient(patient_id, dicom_file.PatientName)
                    new_patient.add_study(new_study)

                    dicom_structure.add_patient(new_patient)
                else:
                    existing_patient = dicom_structure.get_patient(dicom_file.PatientID)
                    if not existing_patient.has_study(dicom_file.StudyInstanceUID):
                        new_series = Series(dicom_file.SeriesInstanceUID)
                        new_series.series_description = dicom_file.get("SeriesDescription")
                        new_series.add_image(new_image)

                        new_study = Study(dicom_file.StudyInstanceUID)
                        new_study.study_description = dicom_file.get("StudyDescription")
                        new_study.add_series(new_series)

                        existing_patient.add_study(new_study)
                    else:
                        existing_study = existing_patient.get_study(dicom_file.StudyInstanceUID)
                        if not existing_study.has_series(dicom_file.SeriesInstanceUID):
                            new_series = Series(dicom_file.SeriesInstanceUID)
                            new_series.series_description = dicom_file.get("SeriesDescription")
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
