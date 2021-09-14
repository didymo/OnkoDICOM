from PySide6 import QtCore, QtGui

import numpy as np
import SimpleITK as sitk
import datetime
import pydicom
import os

from copy import deepcopy
from pydicom.tag import Tag

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from platipy.imaging.registration.linear import linear_registration
from platipy.imaging.visualisation.utils import generate_comparison_colormix, \
    return_slice


# Utility Functions
def point2str(point, precision=1):
    """
    Format a point for printing, based on specified precision with
    trailing zeros. Uniform printing for vector-like data (tuple, numpy
    array, list).

    Args:
        point (vector-like): nD point with floating point coordinates.
        precision (int): Number of digits after the decimal point.
    Return:
        String represntation of the given point "xx.xxx yy.yyy
        zz.zzz...".
    """
    return ' '.join(f'{c:.{precision}f}' for c in point)


def uniform_random_points(bounds, num_points):
    """
    Generate random (uniform withing bounds) nD point cloud.
    Dimension is based on the number of pairs in the bounds input.

    Args:
        bounds (list(tuple-like)): list where each tuple defines the
        coordinate bounds.
        num_points (int): number of points to generate.

    Returns:
        list containing num_points numpy arrays whose coordinates are
        within the given bounds.
    """
    internal_bounds = [sorted(b) for b in bounds]
    # Generate rows for each of the coordinates according to the given
    # bounds, stack into an array and split into a list of points.
    mat = np.vstack([np.random.uniform(b[0], b[1], num_points)
                     for b in internal_bounds])

    return list(mat[:len(bounds)].T)


def target_registration_errors(tx, point_list, reference_point_list):
    """
    Distances between points transformed by the given transformation and
    their location in another coordinate system. When the points are
    only used to evaluate registration accuracy (not used in the
    registration) this is the target registration error (TRE).
    """
    return [np.linalg.norm(np.array(tx.TransformPoint(p)) - np.array(p_ref))
            for p, p_ref in zip(point_list, reference_point_list)]


def print_transformation_differences(tx1, tx2):
    """
    Check whether two transformations are "equivalent" in an arbitrary
    spatial region either 3D or 2D, [x=(-10,10), y=(-100,100), z=(-1000,1000)].
    This is just a sanity check, as we are just looking at the effect of the
    transformations on a random set of points in the region.
    """
    if tx1.GetDimension() == 2 and tx2.GetDimension() == 2:
        bounds = [(-10, 10), (-100, 100)]
    elif tx1.GetDimension() == 3 and tx2.GetDimension() == 3:
        bounds = [(-10, 10), (-100, 100), (-1000, 1000)]
    else:
        raise ValueError('Transformation dimensions mismatch, '
                         'or unsupported transformation dimensionality')
    num_points = 10
    point_list = uniform_random_points(bounds, num_points)
    tx1_point_list = [tx1.TransformPoint(p) for p in point_list]
    differences = target_registration_errors(tx2, point_list, tx1_point_list)
    print(tx1.GetName() + '-' +
          tx2.GetName() +
          f':\tminDifference: {min(differences):.2f} maxDifference: '
          f'{max(differences):.2f}')


def convert_composite_to_affine_transform(composite_transform):
    """
    Converts the sitk.CompositeTransform Object into a
    sitk.AffineTransform Object. This currently assumes that only
    Euler3DTransform and Versor3DRigidTransform are in the stack of the
    sitk.CompositeTransform Object. Purpose is to reduce the amount of
    information down to one matrix.

    Args:
        composite_transform (sitk.CompositeTransform): sitk Object
        containing transforms in a stack-like heap.
    Return:
        combined_affine (sitk.AffineTransform): combined_affine

    """
    # Retrieve the 1st Transform
    transform_type = composite_transform.GetNthTransform(0)

    # Downcast from Composite Transform to Euler3D Transform
    euler3d_transform = transform_type.Downcast()

    # Retrieve the 2nd Transform
    transform_type = composite_transform.GetNthTransform(1)
    # Downcast from Composite Transform to VersorRigid3D Transform
    versor_transform = transform_type.Downcast()

    # Assign Matrices to equations
    A0 = np.asarray(euler3d_transform.GetMatrix()).reshape(3, 3)
    c0 = np.asarray(euler3d_transform.GetCenter())
    t0 = np.asarray(euler3d_transform.GetTranslation())

    A1 = np.asarray(versor_transform.GetMatrix()).reshape(3, 3)
    c1 = np.asarray(versor_transform.GetCenter())
    t1 = np.asarray(versor_transform.GetTranslation())

    combined_mat = np.dot(A0, A1)
    combined_center = c1
    combined_translation = np.dot(A0, t1 + c1 - c0) + t0 + c0 - c1
    combined_affine = sitk.AffineTransform(combined_mat.flatten(),
                                           combined_translation,
                                           combined_center)

    # check_affine_conversion(composite_transform, combined_affine)

    return combined_affine


def check_affine_conversion(composite_transform, combined_affine):
    """
    Checks the conversion from composite transformation to the
    combined affine transformation. Print statements
    shows how much the transformation matrix
    differs between the two.
    Args:
        composite_transform (sitk.CompositeTransform): sitk Object
        containing transforms in a stack-like heap.
        combined_affine (sitk.AffineTransform): sitk Object containing
        transforms in a stack-like heap.

    """
    print('Apply the two transformations to the same point cloud:')
    print('\t', end='')
    print_transformation_differences(composite_transform, combined_affine)

    print('Transform parameters:')
    print('\tComposite transform: ' +
          point2str(composite_transform.GetParameters(), 2))
    print('\tCombined affine: ' +
          point2str(combined_affine.GetParameters(), 2))

    print('Fixed parameters:')
    print('\tComposite transform: ' +
          point2str(composite_transform.GetFixedParameters(), 2))
    print('\tCombined affine: ' +
          point2str(combined_affine.GetFixedParameters(), 2))

    print('combined_affine')
    print(combined_affine)


def convert_combined_affine_to_matrix(combined_affine):
    """
    Conversion of the 3x3 transform matrix from the AffineTransform 
    object(keeping in mind it is a RIGID) to a 4x4 transformation
    matrix where last row is (0, 0, 0, 1).
    """
    A = np.array(combined_affine.GetMatrix()).reshape(3, 3)
    c = np.array(combined_affine.GetCenter())
    t = np.array(combined_affine.GetTranslation())
    overall = np.eye(4)
    overall[0:3, 0:3] = A
    overall[0:3, 3] = -np.dot(A, c) + t + c

    return overall


def write_transform_to_dcm(affine_matrix):
    """
    Function to write data of the top(moving) image respective
    to the base(fixed) image.
    
    This function will require future refacotring when the transform 
    DICOM file becomes in use, as this function only assumes there is 
    one RIGID matrix to be saved.
    """
    patient_dict_container = PatientDictContainer()
    patient_path = patient_dict_container.path

    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")

    top_level_tags_to_copy: list = [
        Tag("PatientName"),
        Tag("PatientID"),
        Tag("StudyDate"),
        Tag("StudyTime"),
        Tag("AccessionNumber"),
        Tag("ReferringPhysicianName"),
        Tag("StudyDescription"),
        Tag("StudyInstanceUID"),
        Tag("StudyID"),
        Tag("PositionReferenceIndicator"),
    ]

    # Get Patient Dataset
    patient_dataset = patient_dict_container.dataset[0]

    # Create a new Dataset
    spatial_registration = pydicom.dataset.Dataset()

    # Copy the Dataset to the new dataset
    for tag in top_level_tags_to_copy:
        # print("Tag ", tag)
        if tag in patient_dataset:
            # print("value of tag in image: ", patient_dataset[tag])
            spatial_registration[tag] = deepcopy(patient_dataset[tag])

    # Get the MovingDictContainer
    moving_dict_container = MovingDictContainer()

    # Conversion of the numpy.ndarray to array of strings
    x = []
    for item in affine_matrix:
        for nested_item in item:
            x.append(str(nested_item))

    # Create a Sequence Item
    matrix_sequence = []
    matrix_sequence_item = pydicom.dataset.Dataset()
    matrix_sequence_item.FrameOfReferenceTransformationMatrixType = 'RIGID'
    matrix_sequence_item.FrameOfReferenceTransformationMatrix = x
    matrix_sequence.append(matrix_sequence_item)

    # Create a Registration Type Code Sequence
    registration_type_code_sequence = []
    reg_type_code_sequence_item = pydicom.dataset.Dataset()
    reg_type_code_sequence_item.CodeValue = "125024"
    reg_type_code_sequence_item.CodingSchemeDesignator = "DCM"
    reg_type_code_sequence_item.CodeMeaning = "Image Content-based Alignment"
    registration_type_code_sequence.append(reg_type_code_sequence_item)

    # Create a Matrix Registration Sequence and add Matrix_Sequence Item
    matrix_registration_sequence = pydicom.dataset.Dataset()
    matrix_registration_sequence.MatrixSequence = matrix_sequence
    matrix_registration_sequence.RegistrationTypeCodeSequence = \
        registration_type_code_sequence

    # Create Reference Image Sequence items
    reference_image_sequences = []
    for x in range(len(moving_dict_container.dataset.keys())):

        try:
            reference_image_sequence_item = pydicom.dataset.Dataset()
            reference_image_sequence_item.ReferencedSOPClassUID = \
                moving_dict_container.dataset[x].SOPClassUID
            reference_image_sequence_item.ReferencedSOPInstanceUID = \
                moving_dict_container.dataset[x].SOPInstanceUID
            reference_image_sequences.append(reference_image_sequence_item)
        except:
            continue

    registration_sequence = pydicom.dataset.Dataset()
    registration_sequence.ReferencedImageSequence = reference_image_sequences
    registration_sequence.FrameOfReferenceUID = \
        patient_dataset.get("FrameOfReferenceUID")
    registration_sequence.MatrixRegistrationSequence = \
        [matrix_registration_sequence]

    # General Information
    spatial_registration.SeriesDate = dicom_date
    spatial_registration.SeriesTime = dicom_time
    spatial_registration.ContentDate = dicom_date
    spatial_registration.ContentTime = dicom_time
    spatial_registration.InstanceCreationDate = dicom_date
    spatial_registration.InstanceCreationTime = dicom_time
    spatial_registration.Modality = "REG"
    spatial_registration.SeriesDescription = "Image Registration"
    spatial_registration.RegistrationSequence = [registration_sequence]
    spatial_registration.SOPClassUID = "1.2.840.10008.5.1.4.1.1.66.1"
    spatial_registration.SOPInstanceUID = \
        patient_dataset.get("SOPInstanceUID")
    spatial_registration.Manufacturer = "OnkoDICOM"
    spatial_registration.StationName = patient_dataset.get("StationName")

    spatial_registration.is_little_endian = True
    spatial_registration.is_implicit_VR = True

    # Place path into Patient->Study folder
    filepath = os.path.join(patient_dict_container.path, 'transform.dcm')

    spatial_registration.save_as(filepath)


def create_fused_model(old_images, new_image):
    """
    Creates the image necessary to display for image fusion.
    """
    fused_image = register_images(old_images, new_image)
    tfm = fused_image[1]
    # Throw Transform Object into function to write dcm file
    combined_affine = convert_composite_to_affine_transform(fused_image[1])
    # test = check_affine_conversion(fused_image[1], combined_affine)
    affine_matrix = convert_combined_affine_to_matrix(combined_affine)
    write_transform_to_dcm(affine_matrix)

    array = sitk.GetArrayFromImage(old_images).shape

    axial_slice_count = array[0]
    coronal_slice_count = array[1]
    sagittal_slice_count = array[1]

    # create colored images
    sp_plane, _, sp_slice = old_images.GetSpacing()
    asp = (1.0 * sp_slice) / sp_plane

    color_axial = {}
    color_sagittal = {}
    color_coronal = {}

    for i in range(axial_slice_count):
        color_axial[i] = \
            get_fused_pixmap(old_images, fused_image[0], asp, i, "axial")

    for i in range(sagittal_slice_count):
        color_sagittal[i] = \
            get_fused_pixmap(old_images, fused_image[0], asp, i, "sagittal")

    for i in range(coronal_slice_count):
        color_coronal[i] = \
            get_fused_pixmap(old_images, fused_image[0], asp, i, "coronal")

    return color_axial, color_sagittal, color_coronal, tfm


# Can be expanded to peform all of platipy's registrations
def register_images(image_1, image_2):
    """
    Registers the moving and fixed image.
    Args:
        image_1 (Image Matrix)
        image_2 (Image Matrix)
    Return:
        img_ct (Array)
        tfm (sitk.CompositeTransform)
    """
    img_ct, tfm = linear_registration(
        image_1,
        image_2,
        shrink_factors=[8],
        smooth_sigmas=[10],
        reg_method='rigid',
        verbose=False
    )
    return img_ct, tfm


def get_fused_pixmap(orig_image, fused_image, aspect, slice_num, view):
    """
    Get a color pixmap.
    :param sitk image: original 3d image
    :param sikt image: fused 3d image
    :param aspect: scaled pixel spacing of first image
    :return: color pixmap.
    """
    # Get dimension /could also input dimensions as parameters
    image_array = sitk.GetArrayFromImage(orig_image)
    if (view == "sagittal"):
        image_slice = return_slice("x", slice_num)

        pixel_array_color = \
            np.array(generate_comparison_colormix([orig_image, fused_image],
                                                  arr_slice=image_slice))

        # resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512, 345, 3))

        # first adjusts rgb (0,1) scale to greyscale (0,255)
        # then converts type and formats it to color.
        qimage2 = \
            QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)),
                         image_array.shape[1], image_array.shape[0],
                         QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)

        pixmap = pixmap.scaled(512,
                               512,
                               QtCore.Qt.IgnoreAspectRatio,
                               QtCore.Qt.SmoothTransformation)
    elif view == "coronal":
        image_slice = return_slice("y", slice_num)

        pixel_array_color = np.array(generate_comparison_colormix(
            [orig_image, fused_image],
            arr_slice=image_slice))

        # resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512, 345, 3))

        # first adjusts rgb (0,1) scale to greyscale (0,255)
        # then converts type and formats it to color.
        qimage2 = QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)),
                               image_array.shape[1],
                               image_array.shape[0],
                               QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)
        pixmap = pixmap.scaled(512,
                               512,
                               QtCore.Qt.IgnoreAspectRatio,
                               QtCore.Qt.SmoothTransformation)
    else:
        image_slice = return_slice("z", slice_num)

        pixel_array_color = np.array(generate_comparison_colormix(
            [orig_image, fused_image],
            arr_slice=image_slice))

        # first adjusts rgb (0,1) scale to greyscale (0,255)
        # then converts type and formats it to color.
        qimage = QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)),
                              image_array.shape[1],
                              image_array.shape[1],
                              QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage)
        pixmap = pixmap.scaled(512,
                               512,
                               QtCore.Qt.IgnoreAspectRatio,
                               QtCore.Qt.SmoothTransformation)

    # Generates an rgb color overlaid image,
    # convert to contiguous array,
    # and also flip the array if it is a coronal (y) or sagittal (x)
    return pixmap


def scaled_size(width, height):
    if width > height:
        height = 512 / width * height
        width = 512
    else:
        width = 512 / height * width
        height = 512
    return width, height
