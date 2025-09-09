import logging
import os
import glob
from pathlib import Path
import SimpleITK as sitk
import numpy as np
from rt_utils import RTStructBuilder, RTStruct

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    reader.SetFileNames(dicom_names)
    return reader.Execute()

# Resample segment to match dicom series
def _resample_seg_to_ct(ct_image: sitk.Image, seg_image: sitk.Image) -> sitk.Image:
    """
    Resample the segmentation image to match the CT image's grid.

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
        raise ValueError(f"Invalid NIfTI directory: {nifti_path}")

    dicom_dir = Path(dicom_path)
    if not dicom_dir.is_dir():
        raise ValueError(f"Invalid DICOM directory: {dicom_path}")

    output_file = Path(output_path)
    if not output_file.parent.is_dir():
        raise ValueError(f"Invalid output directory: {output_file.parent}")

def _process_nifti_file(nifti_image_path: str, dicom_img: sitk.Image, rtstruct: RTStruct) -> None:
    """
    Processes a single NIfTI segmentation file by orienting and resampling it to match
    the provided DICOM image, then adds the resulting mask as a new ROI to the given RTStruct.

    Args:
        nifti_image_path (str): Path to the NIfTI segmentation file (.nii or .nii.gz).
        dicom_img (sitk.Image): The reference DICOM image (SimpleITK Image) to match orientation and spacing.
        rtstruct (RTStruct): The RTStruct object to which the ROI mask will be added.

    Returns:
        None
    """
    nifti_file_name = Path(nifti_image_path).name

    structure_name = Path(nifti_file_name).stem  # handles files with .nii.gz extensions (as returned from totalsegmentator)
    logging.info(f"Converting {nifti_file_name} to RTStruct")

    # load & orient Nifti image
    nifti_img = sitk.DICOMOrient(sitk.ReadImage(nifti_image_path), 'LPS')
    nifti_img.CopyInformation(dicom_img)

    # resample Nifti image & create mask
    aligned_nifti_img = _resample_seg_to_ct(dicom_img, nifti_img)
    nifti_array = sitk.GetArrayFromImage(aligned_nifti_img).astype(bool)
    nifti_array_trans = np.transpose(nifti_array, (1, 2, 0))
    rtstruct.add_roi(mask=nifti_array_trans, name=structure_name)

def nifti_to_rtstruct_conversion(nifti_path: str, dicom_path: str, output_path: str) -> bool:
    """
    Converts NIfTI image files to an RT Struct file based on the corresponding DICOM series.

    Args:
        nifti_path (str): Path to the directory containing NIfTI files.
        dicom_path (str): Path to the directory containing the DICOM series.
        output_path (str): Path to save the generated RTStruct file.

    Returns:
        bool: True if the conversion was successful.

    Raises:
        ValueError: If input paths are invalid or no NIfTI files are found.
        Exception: If an unexpected error occurs during conversion.
    """
    logging.info("Converting NIfTI to RTStruct...")

    _validate_inputs(nifti_path, dicom_path, output_path)

    # Orientate the Dicom image to LPS (Left, Posterior, Superior) standard
    dicom_img = sitk.DICOMOrient(_load_dicom_series_as_sitk(dicom_path), 'LPS')

    # Build or load the rtstruct
    if os.path.exists(output_path):
        logging.info(f"Loading existing RTStruct: {output_path}")
        rtstruct = RTStructBuilder.create_from(
            rt_struct_path=output_path,
            dicom_series_path=dicom_path
        )
    else:
        logging.info("Creating new RTStruct")
        rtstruct = RTStructBuilder.create_new(dicom_series_path=dicom_path)

    # Get the list of nifti files from path
    nifti_files_list: list[str] = glob.glob(os.path.join(nifti_path, "*.nii.gz"))

    if not nifti_files_list:
        raise ValueError(f"No NIfTI files found at: {nifti_path}")

    try:
        for img_path in nifti_files_list:
            _process_nifti_file(str(img_path), dicom_img, rtstruct)
        rtstruct.save(output_path)
        return True
    except Exception as e:
        logging.error(f"Conversion failed: {type(e).__name__}: {e}")
        raise