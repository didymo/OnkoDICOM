import os

from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from src.Model.DICOMStructure import DICOMStructure, Patient, Study, \
    Series, Image


def get_dicom_structure(path, interrupt_flag, progress_callback):
    """
    Searches the given directory and creates a Patient>Study>Series>Image
    structure based on the DICOM files in the directory and subdirectories.

    :param path: The root directory to search from.
    :param interrupt_flag: A threading.Event() flag to indicate whether
        or not the process has been interrupted.
    :param progress_callback: A function that receives the progress of
        the current search.
    :return: Complete DICOMStructure object with associated DICOM files
    """

    dicom_structure = DICOMStructure()

    files_searched = 0

    files_with_no_patient_id = 1

    for root, dirs, files in os.walk(path, topdown=True):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for file in files:
            if file[0] == '.':
                break
            if interrupt_flag.is_set():
                return

            # The progress is updated first because the total files
            # represents ALL files inside the selected directory, not just
            # the DICOM files. Otherwise, most files would be skipped and
            # the progress would be inaccurate.
            files_searched += 1
            progress_callback.emit("%s" % files_searched)

            # Fix to program crashing when encountering DICOMDIR files
            if file == "DICOMDIR":
                continue

            file_path = root + os.sep + file
            try:
                dicom_file = dcmread(file_path)
            except (InvalidDicomError, FileNotFoundError, PermissionError):
                pass
            else:
                if 'PatientID' in dicom_file:
                    patient_id = dicom_file.PatientID
                else:
                    patient_id = "no_id_" + str(files_with_no_patient_id)
                    files_with_no_patient_id += 1

                if "SOPInstanceUID" in dicom_file \
                        and "SOPClassUID" in dicom_file \
                        and "Modality" in dicom_file:
                    new_image = Image(file_path,
                                      dicom_file.SOPInstanceUID,
                                      dicom_file.SOPClassUID,
                                      dicom_file.Modality)
                    if not dicom_structure.has_patient(patient_id):
                        # TODO there is definitely a more efficient way of
                        #  doing this
                        new_series = get_series(dicom_file, new_image)

                        new_study = Study(dicom_file.StudyInstanceUID)
                        new_study.study_description = dicom_file.get(
                            "StudyDescription")
                        new_study.add_series(new_series)

                        new_patient = Patient(patient_id,
                                              dicom_file.PatientName)
                        new_patient.add_study(new_study)

                        dicom_structure.add_patient(new_patient)
                    else:
                        existing_patient = dicom_structure.get_patient(
                            dicom_file.PatientID)
                        if not existing_patient.has_study(
                                dicom_file.StudyInstanceUID):
                            new_series = get_series(dicom_file, new_image)

                            new_study = Study(dicom_file.StudyInstanceUID)
                            new_study.study_description = dicom_file.get(
                                "StudyDescription")
                            new_study.add_series(new_series)

                            existing_patient.add_study(new_study)
                        else:
                            existing_study = existing_patient.get_study(
                                dicom_file.StudyInstanceUID)
                            if not existing_study.has_series(
                                    dicom_file.SeriesInstanceUID):
                                new_series = get_series(dicom_file, new_image)

                                existing_study.add_series(new_series)
                            else:
                                existing_series = existing_study.get_series(
                                    dicom_file.SeriesInstanceUID)
                                if not existing_series.has_image(
                                        dicom_file.SOPInstanceUID):
                                    existing_series.series_description = \
                                        dicom_file.get("SeriesDescription")
                                    existing_series.add_image(new_image)

    return dicom_structure


def get_series(dicom_file, new_image, existing_series=None):
    new_series = Series(dicom_file.SeriesInstanceUID)
    new_series.series_description = dicom_file.get(
        "SeriesDescription")
    new_series.add_image(new_image)
    if "FrameOfReferenceUID" in dicom_file:
        new_series.frame_of_reference_uid = dicom_file.FrameOfReferenceUID
    if new_image.modality == "RTSTRUCT":
        if "ReferencedFrameOfReferenceSequence" in dicom_file:
            frame = dicom_file.ReferencedFrameOfReferenceSequence
            if "RTReferencedStudySequence" in frame[0]:
                study = frame[0].RTReferencedStudySequence[0]
                if "RTReferencedSeriesSequence" in study:
                    if "SeriesInstanceUID" in \
                            study.RTReferencedSeriesSequence[0]:
                        series = study.RTReferencedSeriesSequence[0]
                        new_series.referenced_image_series_uid = \
                            series.SeriesInstanceUID
        else:
            new_series.referenced_image_series_uid = ''
    elif new_image.modality == "RTPLAN" or new_image.modality == "RTDOSE":
        if "ReferencedStructureSetSequence" in dicom_file:
            new_series.referenced_rtss_uid = \
                dicom_file.ReferencedStructureSetSequence[0].\
                    ReferencedSOPInstanceUID
        else:
            new_series.referenced_rtss_uid = ''

        if new_image.modality == "RTDOSE":
            if "ReferencedRTPlanSequence" in dicom_file:
                new_series.refenced_rtplan_uid = \
                    dicom_file.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID
            else:
                new_series.refenced_rtplan_uid = ''
    return new_series


if __name__ == "__main__":
    ds = get_dicom_structure("XR.Identified")
    print(ds.get_files())
