import pydicom
from PySide6 import QtCore, QtGui

import numpy as np
import SimpleITK as sitk
import collections
import datetime
import random
from copy import copy as shallowcopy
from copy import deepcopy
from pydicom import Dataset, Sequence
from pydicom.tag import Tag

from src.Model.PatientDictContainer import PatientDictContainer

from platipy.dicom.io.crawl import process_dicom_directory
from platipy.imaging.registration.linear import linear_registration
from platipy.imaging.visualisation.utils import (generate_comparison_colormix, return_slice)


def dicom_crawler(filepath, overwrite, output):
    process_dicom_directory(filepath,
                            overwrite_existing_files=overwrite,
                            output_directory=output)


def create_fused_model(old_images, new_image):
    print("fuseTest00")

    # fuse images
    fused_image = register_images(old_images, new_image)

    print("Fused_Image Object")
    print(type(fused_image[1]))
    # Throw Transform Object into function to write dcm file
    write_transform_to_dcm(fused_image[1]);

    print("fuseTest01")

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

    print("fuseTest1")
    for i in range(axial_slice_count):
        color_axial[i] = get_fused_pixmap(old_images, fused_image[0], asp, i, "axial")

    print("fuseTest2")
    for i in range(sagittal_slice_count):
        color_sagittal[i] = get_fused_pixmap(old_images, fused_image[0], asp, i, "sagittal")

    print("fuseTest3")
    for i in range(coronal_slice_count):
        color_coronal[i] = get_fused_pixmap(old_images, fused_image[0], asp, i, "coronal")

    return color_axial, color_sagittal, color_coronal


# Can be expanded to peform all of platipy's registrations
def register_images(image_1, image_2):
    img_ct, tfm = linear_registration(
        image_1,
        image_2,
        shrink_factors=[8],
        smooth_sigmas=[10],
        reg_method='rigid',
        verbose=False
    )
    return img_ct, tfm


class TransformObject():
    def __init__(self, _transform_type, _matrix, _center, _translation):
        self.transform_type = _transform_type
        self.matrix = _matrix
        self.center = _center
        self.translation = _translation


def write_transform_to_dcm(transform_object):

    patient_dict_container = PatientDictContainer()
    patient_path = patient_dict_container.path

    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")

    print('Test Write Transform to dcm')

    suffix = '.dcm'

    top_level_tags_to_copy: list = [Tag("PatientName"),
                                    Tag("PatientID"),
                                    Tag("PatientBirthDate"),
                                    Tag("PatientSex"),
                                    Tag("StudyDate"),
                                    Tag("StudyTime"),
                                    Tag("ReferringPhysicianName"),
                                    Tag("StudyDescription"),
                                    Tag("StudyInstanceUID"),
                                    Tag("StudyID"),
                                    Tag("RequestingService"),
                                    Tag("PatientAge"),
                                    Tag("PatientSize"),
                                    Tag("PatientWeight"),
                                    Tag("MedicalAlerts"),
                                    Tag("Allergies"),
                                    Tag("PregnancyStatus"),
                                    Tag("FrameOfReferenceUID"),
                                    Tag("PositionReferenceIndicator"),
                                    Tag("InstitutionName"),
                                    Tag("InstitutionAddress")
                                    ]

    # Get Patient Dataset
    patient_dataset = patient_dict_container.dataset[0]
    # print(patient_dataset)

    # Create a new Dataset
    new_dataset = pydicom.Dataset()

    # Copy the Dataset to the new dataset
    for tag in top_level_tags_to_copy:
        # print("Tag ", tag)
        if tag in patient_dataset:
            # print("value of tag in image: ", patient_dataset[tag])
            new_dataset[tag] = deepcopy(patient_dataset[tag])

    print('Print the Matrix Sequence Meta Tag')
    print(new_dataset.data_element('MatrixSeqeuence'))

    # for x in range(transform_object.GetNumberOfTransforms()):
    #     sitk

    transform_type = transform_object.GetNthTransform(0)
    euler3d_transform = transform_type.Downcast()

    print('Type')
    print(euler3d_transform.GetName())
    print('Matrix')
    print(euler3d_transform.GetMatrix())
    print('Center')
    print(euler3d_transform.GetCenter())
    print('Translation')
    print(euler3d_transform.GetTranslation())

    t_object = TransformObject(euler3d_transform.GetName(),
                               euler3d_transform.GetMatrix(),
                               euler3d_transform.GetCenter(),
                               euler3d_transform.GetTranslation())
    print('Adding RIGID to DICOM')
    new_dataset.add_new(0x0070030C,'CS','RIGID')

    print('Adding Matrices to DICOM')
    new_dataset.add_new(0x300600c6, 'DS', euler3d_transform.GetMatrix())
    print('Test if the element has been entered')
    print(new_dataset)


def get_fused_pixmap(orig_image, fused_image, aspect, slice_num, view):
    # Get a color pixmap.
    # :param sitk image: original 3d image
    # :param sikt image: fused 3d image
    # :param aspect: scaled pixel spacing of first image
    # :return: color pixmap.

    # Get dimension /could also input dimensions as parameters
    image_array = sitk.GetArrayFromImage(orig_image)

    axial_width, axial_height = scaled_size(image_array.shape[1] * aspect, image_array.shape[2])
    coronal_width, coronal_height = scaled_size(image_array.shape[1], image_array.shape[0] * aspect)
    sagittal_width, sagittal_height = scaled_size(image_array.shape[2] * aspect, image_array.shape[0])

    # get an array in the form (:, i, :), (i, :, :), (:,:,i)
    if (view == "sagittal"):
        image_slice = return_slice("x", slice_num)

        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice=image_slice))

        # pixel_array_color = np.array(
        #                               np.flip(
        #                                   generate_comparison_colormix([orig_image, fused_image],
        #                                   arr_slice = image_slice)))

        # resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512, 345, 3))

        # first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color.
        qimage2 = QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[0],
                               QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)

        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

    ##########################################
    elif view == "coronal":
        image_slice = return_slice("y", slice_num)

        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice=image_slice))

        # resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512, 345, 3))

        # first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color.
        qimage2 = QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[0],
                               QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)

        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    else:
        image_slice = return_slice("z", slice_num)

        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice=image_slice))

        # first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color.
        qimage = QtGui.QImage(((255 * pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[1],
                              QtGui.QImage.Format_RGB888)

        # Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage)

        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

    # Generates an rgb color overlaid image,
    # convert to contiguous array, and also flip the array if it is a coronal (y) or sagittal (x)

    return pixmap


def scaled_size(width, height):
    if width > height:
        height = 512 / width * height
        width = 512
    else:
        width = 512 / height * width
        height = 512
    return width, height
