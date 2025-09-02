import os
import logging
from pydicom import dcmread
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.GetPatientInfo import DicomTree
from src.Model.ROI import ordered_list_rois

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def gather_all_files(directory: str) -> list[str]:
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    ]

def parse_rtss_and_images(rtss_path: str, directory: str) -> dict:
    """Parses RTSTRUCT file and associated DICOM images.

    This function extracts comprehensive information from an RTSTRUCT file
    and its corresponding DICOM images, including ROI details, contour data,
    and pixel lookup tables.

    Args:
        rtss_path: Path to the RTSTRUCT DICOM file.
        directory: Directory containing associated DICOM images.

    Returns:
        A dictionary containing parsed RTSTRUCT and image metadata.
    """
    ds = dcmread(rtss_path)
    files = gather_all_files(directory)
    read_data, _ = ImageLoading.get_datasets(files)
    rois = ImageLoading.get_roi_info(ds)
    raw_contour, num_points = ImageLoading.get_raw_contour_data(ds)
    pixluts = ImageLoading.get_pixluts(read_data)
    tree = DicomTree(None).dataset_to_dict(ds)
    roi_list = ordered_list_rois(rois)

    return {
        "dataset_rtss": ds,
        "rois": rois,
        "raw_contour": raw_contour,
        "num_points": num_points,
        "pixluts": pixluts,
        "dict_dicom_tree_rtss": tree,
        "list_roi_numbers": roi_list,
    }

def load_rtss_file_to_patient_dict(container: PatientDictContainer) -> None:
    rtss_path = container.filepaths["rtss"]
    if not rtss_path:
        logger.error("No rtss file found")
        return

    data = parse_rtss_and_images(rtss_path, container.path)
    # set everything in one place, skip internal-only keys if desired
    for key, val in data.items():
        if key == "dataset_rtss":
            continue
        container.set(key, val)
    container.set("selected_rois", [])