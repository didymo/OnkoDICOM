import os
from pydicom import dcmread
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.GetPatientInfo import DicomTree
from src.Model.ROI import ordered_list_rois


# Loads an updated RTStruct (rtss) file into the patient dictionary
def load_rtss_file_to_patient_dict(patient_dict_container: PatientDictContainer) -> None:
    dataset_rtss = None
    read_data_dict = None
    selected_files = []

    if patient_dict_container.filepaths["rtss"] is not None:
        dataset_rtss = dcmread(patient_dict_container.filepaths["rtss"])
        for entry in os.listdir(patient_dict_container.path):
            full_path = os.path.join(patient_dict_container.path, entry)
            if os.path.isfile(full_path):
                selected_files.append(full_path)

        read_data_dict, file_names_dict = ImageLoading.get_datasets(
            selected_files
        )
    else:
        print("No rtss file")

    rois = ImageLoading.get_roi_info(dataset_rtss)
    # print("rois:", rois)

    dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(
        dataset_rtss
    )
    patient_dict_container.set("raw_contour", dict_raw_contour_data)

    dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

    # Add RTSS values to PatientDictContainer
    patient_dict_container.set("rois", rois)
    patient_dict_container.set("raw_contour", dict_raw_contour_data)
    patient_dict_container.set("num_points", dict_numpoints)
    patient_dict_container.set("pixluts", dict_pixluts)

    # Set some patient dict container attributes
    ordered_dict = DicomTree(None).dataset_to_dict(dataset_rtss)
    patient_dict_container.set("dict_dicom_tree_rtss", ordered_dict)

    patient_dict_container.set(
        "list_roi_numbers",
        ordered_list_rois(patient_dict_container.get("rois")))
    patient_dict_container.set("selected_rois", [])