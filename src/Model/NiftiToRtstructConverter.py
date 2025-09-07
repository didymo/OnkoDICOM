import logging
import os
import glob
from pathlib import Path

import SimpleITK as sitk
import numpy as np
from rt_utils import RTStructBuilder

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
        raise ValueError(f"Invalid NIfTI directory: {nifti_path}")

    dicom_dir = Path(dicom_path)
    if not dicom_dir.is_dir():
        raise ValueError(f"Invalid DICOM directory: {dicom_path}")

    output_file = Path(output_path)
    if not output_file.parent.is_dir():
        raise ValueError(f"Invalid output directory: {output_file.parent}")

def nifti_to_rtstruct_conversion(nifti_path: str, dicom_path: str, output_path: str) -> bool:

    """Converts NIfTI image files to an RT Struct file based on the corresponding
    DICOM series.

    Args:
        nifti_path: Path to the directory containing NIfTI files.
        dicom_path: Path to the directory containing the DICOM series.
        output_path: Path to save the generated RTStruct file.

    Returns:
        True if the conversion was successful.

    Raises:
        FileNotFoundError: If the DICOM series is not found.
        ValueError: If input paths are invalid or no NIfTI files are found.
        RuntimeError: If a NIfTI file cannot be read or processed, or if the
        RTStruct cannot be saved.
    """

    logging.info("Converting NIfTI to RTStruct...")
    print("Converting NIfTI to RTStruct...")

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
            logging.error(f"No NIfTI files found at: {nifti_path}")
            raise ValueError(f"No NIfTI files found at: {nifti_path}")

        for img in nifti_files_list:
            try:
                # Get the file name from path (img)
                nifti_file_name = os.path.basename(img)

                # Get structure name
                structure_name = os.path.splitext(os.path.splitext(nifti_file_name)[0])[0]

                # Log progress
                logging.info(f"Converting {os.path.basename(img)} to DICOM RTStruct")

                # Load segmentation nifti image
                nifti_img = sitk.ReadImage(img)

                # Orientate nifti image to the dicom standard
                nifti_img = sitk.DICOMOrient(nifti_img, 'LPS')

                # Ensure orientations match
                nifti_img.CopyInformation(dicom_img)

                # Resample segmentation to match CT
                aligned_seg_image = _resample_seg_to_ct(dicom_img, nifti_img)

                # Access image data as array and convert to bool type for mask rt_util input
                nifti_array = sitk.GetArrayFromImage(aligned_seg_image).astype(bool)

                # Transpose the array before passing to rt_util as expects (y, x, z) configuration
                nifti_array = np.transpose(nifti_array, (1, 2, 0))

                rtstruct.add_roi(mask=nifti_array, name=structure_name)
            except RuntimeError as e:
                logging.error(f"Error reading or processing NIfTI file: {img}: {e}")
                raise # Re-raise the exception after logging
            except Exception as e:
                logging.error(f"An unexpected error occurred while processing NIfTI file {img}: {e}")
                raise

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

