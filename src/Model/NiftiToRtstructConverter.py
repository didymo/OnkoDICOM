import logging
import os
import glob
from pathlib import Path
import csv
import SimpleITK as sitk
import numpy as np
from rt_utils import RTStructBuilder
from src.Controller.PathHandler import data_path

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
    Resample the Nifti segmentation image to match the CT image's grid

    :param ct_image:
    :param seg_image:
    :return: SimpleITK.Image
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
    """
    Load a mapping from Nifti filenames to ROI names
    for auto segmentations.

    :return: dict where key=filename, value=ROI name
    """
    mapping = {}
    with open(data_path('totalSegmentOrganNames.csv'), 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header if present
        for row in reader:
            if len(row) >= 4:
                roi_name = row[0].strip()
                filename = row[2].strip()
                mapping[filename] = roi_name
    return mapping

def _same_geometry(img1: sitk.Image, img2: sitk.Image) -> bool:
    """Checks if two SimpleITK images have the same geometry.

    Compares size, spacing, origin, and direction of two images.

    Args:
        img1: The first SimpleITK image.
        img2: The second SimpleITK image.

    Returns:
        True if the images have the same geometry, False otherwise.
    """
    return (
        img1.GetSize() == img2.GetSize() and
        np.allclose(img1.GetSpacing(), img2.GetSpacing()) and
        np.allclose(img1.GetOrigin(), img2.GetOrigin()) and
        np.allclose(img1.GetDirection(), img2.GetDirection())
    )

def _ensure_lps_orientation(img: sitk.Image, name: str = "image") -> sitk.Image:
    """Ensures the image is in LPS orientation.

    Checks the orientation of the input SimpleITK image and converts it to the
    Dicom Standard of LPS (Left, Posterior, Superior) if necessary.

    Args:
        img: The SimpleITK image.
        name: The name of the image (for logging).

    Returns:
        The image in LPS orientation.
    """
    orient = sitk.DICOMOrientImageFilter_GetOrientationFromDirectionCosines(img.GetDirection())
    if orient != "LPS":
        logging.info(f"{name} orientation is {orient}, converting to LPS")
        return sitk.DICOMOrient(img, "LPS")
    return img

def nifti_to_rtstruct_conversion(nifti_path: str, dicom_path: str, output_path: str) -> bool:

    """Converts Nifti image files to an RT Struct file based on the corresponding
    DICOM series.

    Args:
        nifti_path: Path to the directory containing Nifti files.
        dicom_path: Path to the directory containing the DICOM series.
        output_path: Path to save the generated RTStruct file.

    Returns:
        True if the conversion was successful.

    Raises:
        FileNotFoundError: If the DICOM series is not found.
        ValueError: If input paths are invalid or no Nifti files are found.
        RuntimeError: If a Nifti file cannot be read or processed, or if the
        RTStruct cannot be saved.
    """

    logging.info("Converting Nifti to RTStruct...")

    try:
        # Validate inputs
        _validate_inputs(nifti_path, dicom_path, output_path)

        # Load the DICOM series as image using SimpleITK
        dicom_img = _load_dicom_series_as_sitk(dicom_path)

        # Orientate the dicom image to dicom standard (Left, Posterior, Superior)
        dicom_img = sitk.DICOMOrient(dicom_img, 'LPS')

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

        # Raise error if no Nifti files found
        if not nifti_files_list:
            logging.error(f"No Nifti files found at: {nifti_path}")
            raise ValueError(f"No Nifti files found at: {nifti_path}")

        # Load CSV name mapping
        segment_name_map = _load_segment_name_mapping()

        for img in nifti_files_list:
            try:
                nifti_img = sitk.ReadImage(img)
                nifti_file_name = Path(img).stem.replace(".nii", "")

                # Skip empty masks
                if not np.any(sitk.GetArrayFromImage(nifti_img)):
                    logging.info(f"Skipping empty mask: {nifti_file_name}")
                    continue

                # Skip images that are not 3D
                if nifti_img.GetDimension() != 3:
                    logging.warning(f"Skipping {nifti_file_name}: not 3D")
                    continue

                # Look up ROI name from CSV mapping
                structure_name = segment_name_map.get(nifti_file_name, nifti_file_name)

                # If name not in csv append '_TS' to nifti file name
                if structure_name == nifti_file_name:
                    structure_name = f"{structure_name}_TS"

                logging.info(f"Converting {nifti_file_name}.nii.gz to ROI: {structure_name}")

                nifti_img = _ensure_lps_orientation(nifti_img, nifti_file_name)

                if not _same_geometry(dicom_img, nifti_img):
                    try:
                        # Resample the segment to match the image geometry
                        nifti_img = _resample_seg_to_ct(dicom_img, nifti_img)
                        # Validate resampling result
                        if not _same_geometry(dicom_img, nifti_img):
                            logging.error(
                                f"Geometry mismatch after resampling for {nifti_file_name}.nii.gz"
                            )
                            continue # Skip ROI due to geometry mismatch
                    except Exception as e:
                        logging.error(f"Resampling failed for {nifti_file_name}.nii.gz: {e}")
                        continue # Skip ROI due to resampling error

                # Access image data as array and convert to bool type for mask rt_util input
                nifti_array = sitk.GetArrayFromImage(nifti_img).astype(bool)

                # Transpose from sitK (z, y, x) before passing to rt_util as expects (y, x, z) configuration
                nifti_array = np.transpose(nifti_array, (1, 2, 0))

                rtstruct.add_roi(mask=nifti_array, name=structure_name)

            except Exception as e:
                logging.error(f"Error processing {img}: {e}")
                continue

        rtstruct.save(output_path)
        return True

    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {e}")
        raise
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        raise
    except RuntimeError as e:
        logging.error(f"RuntimeError: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {type(e).__name__}: {e}")
        raise

