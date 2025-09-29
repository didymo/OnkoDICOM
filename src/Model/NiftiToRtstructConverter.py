import logging
import os
import glob
from pathlib import Path
import csv
import SimpleITK as sitk
import numpy as np
from rt_utils import RTStructBuilder, RTStruct
from src.Controller.PathHandler import data_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function loads a dicom series at dir as SimpleITK image
def _load_dicom_series_as_sitk(dicom_folder: str) -> sitk.Image:
    """
    loads a dicom series at the specified directory
    path as SimpleITK image

    :param dicom_folder:
    :return: SimpleITK.Image
    """
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_folder)
    if not dicom_names:
        raise FileNotFoundError(f"No valid Dicom series found in {dicom_folder}")
    reader.SetFileNames(dicom_names)
    return reader.Execute()

# Resample segment to match dicom series
def _resample_seg_to_ct(ct_image: sitk.Image, seg_image: sitk.Image) -> sitk.Image:
    """
    Resample the Nifti segmentation image to match the CT image's grid

    Args:
        ct_image (sitk.Image): The reference DICOM image
        seg_image (sitk.Image): The Nifti image to be resampled

    Returns:
         Resamples SimpleITK.Image
    """
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(ct_image)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    resample.SetTransform(sitk.Transform())
    return resample.Execute(seg_image)

def _validate_inputs(nifti_path: str, dicom_path: str, output_path: str) -> None:
    """Validates the input paths."""
    nifti_dir = Path(nifti_path)
    if not nifti_dir.is_dir():
        raise ValueError(f"Invalid Nifti directory: {nifti_path}")

    dicom_dir = Path(dicom_path)
    if not dicom_dir.is_dir():
        raise ValueError(f"Invalid DICOM directory: {dicom_path}")

    output_file = Path(output_path)
    if not output_file.parent.is_dir():
        raise ValueError(f"Invalid output directory: {output_file.parent}")

def _load_segment_name_mapping() -> dict[str, str]:
    """Loads a mapping from Nifti filenames to ROI names.

    Reads the 'segmentation_lists.csv' file to create a dictionary mapping
    Nifti filenames (without extension) to ROI names.  The CSV file is
    expected to have at least four columns, with the ROI name in the third
    column and the filename in the fourth.

    Returns:
        A dictionary where keys are Nifti filenames (without extension) and
        values are corresponding ROI names.  Returns an empty dictionary if
        the CSV file is not found or if an error occurs during parsing.
    """
    csv_path = data_path('segmentation_lists.csv')
    if not os.path.exists(csv_path):
        logger.warning(f"Segmentation name mapping file not found: {csv_path}")
        return {}

    mapping = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header row if present
            for row in reader:
                if len(row) >= 4:
                    roi_name = row[2].strip()
                    filename = row[3].strip()
                    mapping[filename] = roi_name
                else:
                    logger.warning(f"Invalid row in CSV: {row}")
    except Exception as e:
        logger.exception(f"Error loading segmentation name mapping: {e}")
        return {}

    return mapping

def _valid_nifti_data(nifti_image_name: str, nifti_img: sitk.Image, nifti_array: np.ndarray) -> bool:
    """Checks if the Nifti image data is valid for conversion.

    Validates the Nifti image and its corresponding NumPy array to ensure
    they meet the requirements for conversion to RTSTRUCT.  Specifically,
    it checks if the mask is empty and if the image is 3D.

    Args:
        nifti_img: The Nifti image (SimpleITK Image).
        nifti_array: The NumPy array representation of the image.

    Returns:
        True if the data is valid, False otherwise.
    """
    # Skip if mask is empty
    if not np.any(nifti_array):
        logger.warning(f"Skipping {nifti_image_name}: Mask is empty.")
        return False

    # Skip images that are not 3D
    if nifti_img.GetDimension() != 3:
        logger.warning(f"Skipping {nifti_image_name}: Not 3D")
        return False

    return True

def _process_nifti_file(nifti_image_path: str, dicom_img: sitk.Image, rtstruct: RTStruct, segment_name_map: dict[str, str]) -> None:
    """
    Processes a single Nifti segmentation file by orienting and resampling it to match
    the provided DICOM image, then adds the resulting mask as a new ROI to the given RTStruct.

    Args:
        nifti_image_path (str): Path to the Nifti segmentation file (.nii or .nii.gz).
        dicom_img (sitk.Image): The reference DICOM image (SimpleITK Image) to match orientation and spacing.
        rtstruct (RTStruct): The RTStruct object to which the ROI mask will be added.

    Returns:
        None
    """
    nifti_image_name =Path(nifti_image_path).name.replace(".nii.gz", "").replace(".nii", "")

    # Remap structure naming
    structure_name = segment_name_map.get(nifti_image_name, nifti_image_name)

    # Skip existing ROIs
    if structure_name in rtstruct.get_roi_names():
        logger.warning(f"Skipping {nifti_image_name}: ROI already exists")
        return

    logger.info(f"Converting {nifti_image_name} to RTStruct")

    # Load & orient Nifti image
    nifti_img = sitk.DICOMOrient(sitk.ReadImage(nifti_image_path), 'LPS')

    # Check nifti data is valid before saving to rtstruct
    if not _valid_nifti_data(nifti_image_name, nifti_img, sitk.GetArrayFromImage(nifti_img)):
        return

    nifti_img.CopyInformation(dicom_img)

    # Resample Nifti image & create mask
    aligned_nifti_img = _resample_seg_to_ct(dicom_img, nifti_img)
    nifti_array = sitk.GetArrayFromImage(aligned_nifti_img).astype(bool)

    # The SimpleITK array is in (slices, rows, columns) order.
    # We transpose to (rows, columns, slices) so that the image data aligns with the expected CT/DICOM layout.
    nifti_array_transposed = np.transpose(nifti_array, (1, 2, 0))

    rtstruct.add_roi(mask=nifti_array_transposed, name=structure_name)

def nifti_to_rtstruct_conversion(nifti_path: str, dicom_path: str, output_path: str) -> bool:

    """Converts Nifti image files to an RT Struct file based on the corresponding
    DICOM series.

    Args:
        nifti_path (str): Path to the directory containing Nifti files.
        dicom_path (str): Path to the directory containing the DICOM series.
        output_path (str): Path to save the generated RTStruct file.

    Returns:
        bool: True if the conversion was successful.

    Raises:
        ValueError: If input paths are invalid or no Nifti files are found.
        Exception: If an unexpected error occurs during conversion.
    """
    logger.info("Converting Nifti to RTStruct...")

    _validate_inputs(nifti_path, dicom_path, output_path)

    # Orientate the Dicom image to LPS (Left, Posterior, Superior) standard
    dicom_img = sitk.DICOMOrient(_load_dicom_series_as_sitk(dicom_path), 'LPS')

    # Build or load the rtstruct
    if os.path.exists(output_path):
        logger.info(f"Loading existing RTStruct: {output_path}")
        rtstruct = RTStructBuilder.create_from(
            rt_struct_path=output_path,
            dicom_series_path=dicom_path
        )
    else:
        logger.info("Creating new RTStruct")
        rtstruct = RTStructBuilder.create_new(dicom_series_path=dicom_path)

    # Get the list of nifti files from path (handles .nii and .nii.gz for robustness)
    nifti_files_list: list[str] = glob.glob(os.path.join(nifti_path, "*.nii.gz"))
    nii_files_list: list[str] = glob.glob(os.path.join(nifti_path, "*.nii"))
    nifti_files_list.extend(nii_files_list)

    # Load CSV name mapping
    segment_name_map = _load_segment_name_mapping()

    if not nifti_files_list:
        raise ValueError(f"No Nifti files found at: {nifti_path}")

    try:
        for img_path in nifti_files_list:
            _process_nifti_file(str(img_path), dicom_img, rtstruct, segment_name_map)
        rtstruct.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Conversion failed: {type(e).__name__}: {e}")
        raise