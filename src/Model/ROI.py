import collections
import datetime
import random
from pathlib import Path
from copy import copy as shallowcopy
from copy import deepcopy

import pydicom
from pydicom.uid import generate_uid, ImplicitVRLittleEndian
from pydicom.dataset import FileMetaDataset, validate_file_meta
from pydicom import Dataset, Sequence
from pydicom.tag import Tag
from src.Model.CalculateImages import *
from src.Model.PatientDictContainer import PatientDictContainer


def rename_roi(rtss, roi_id, new_name):
    """
    Renames the given Region of Interest. Creates a csv file storing all the
    renamed ROIs for the given RTSTRUCT file.
    :param rtss: The RTSTRUCT file.
    :param roi_id: ID the structure produced by ImageLoading.get_rois(..)
    :param new_name: The structure's new name
    """
    for sequence in rtss.StructureSetROISequence:
        if sequence.ROINumber == roi_id:
            sequence.ROIName = new_name

    return rtss


def delete_list_of_rois(rtss, rois_to_delete):
    """
    Call the delete_roi function for each ROI in the given list.
    :param rtss: Dataset of RTSS.
    :param rois_to_delete: List of ROI names.
    :return: Updated RTSS with deleted ROIs.
    """
    for roi_name in rois_to_delete:
        rtss = delete_roi(rtss, roi_name)

    return rtss


def delete_roi(rtss, roi_name):
    """
    Delete ROI by name

    :param rtss: dataset of RTSS
    :param roi_name: ROIName
    :return: rtss, updated rtss dataset
    """
    # ROINumber
    roi_number = -1
    # Delete related StructureSetROISequence element
    for i, elem in enumerate(rtss.StructureSetROISequence):
        if elem.ROIName == roi_name:
            roi_number = rtss.StructureSetROISequence[i].ROINumber
            del rtss.StructureSetROISequence[i]

    # Delete related ROIContourSequence element
    for i, elem in enumerate(rtss.ROIContourSequence):
        if elem.ReferencedROINumber == roi_number:
            del rtss.ROIContourSequence[i]

    # Delete related RTROIObservationsSequence element
    for i, elem in enumerate(rtss.RTROIObservationsSequence):
        if elem.ReferencedROINumber == roi_number:
            del rtss.RTROIObservationsSequence[i]

    return rtss


def add_to_roi(rtss, roi_name, roi_coordinates, data_set):
    """
        Add new contour image sequence ROI to rtss

        :param rtss: dataset of RTSS
        :param roi_name: ROIName
        :param roi_coordinates: Coordinates of pixels for new ROI
        :param data_set: Data Set of selected DICOM image file
        :return: rtss, with added ROI
    """

    # Creating a new ROIContourSequence, ContourSequence, ContourImageSequence
    contour_sequence = Sequence([Dataset()])
    contour_image_sequence = Sequence([Dataset()])

    number_of_contour_points = len(roi_coordinates) / 3
    referenced_sop_class_uid = data_set.SOPClassUID
    referenced_sop_instance_uid = data_set.SOPInstanceUID

    existing_roi_number = None
    for item in rtss["StructureSetROISequence"]:
        if item.ROIName == roi_name:
            existing_roi_number = item.ROINumber

    position = None

    # Get the index of the ROI
    for index, contour in enumerate(rtss.ROIContourSequence):
        if contour.ReferencedROINumber == existing_roi_number:
            position = index

    new_contour_number = len(
        rtss.ROIContourSequence[position].ContourSequence) + 1

    # ROI Sequence
    for contour in contour_sequence:
        # if data_set.get("ReferencedImageSequence"):
        contour.add_new(Tag("ContourImageSequence"),
                        "SQ", contour_image_sequence)

        # Contour Sequence
        for contour_image in contour_image_sequence:
            contour_image.add_new(Tag("ReferencedSOPClassUID"), "UI",
                                  referenced_sop_class_uid)  # CT Image Storage
            contour_image.add_new(Tag("ReferencedSOPInstanceUID"), "UI",
                                  referenced_sop_instance_uid)

        contour.add_new(Tag("ContourNumber"), "IS", new_contour_number)
        if not _is_closed_contour(roi_coordinates):
            contour.add_new(Tag("ContourGeometricType"), "CS", "OPEN_PLANAR")
            contour.add_new(Tag("NumberOfContourPoints"), "IS",
                            number_of_contour_points)
            contour.add_new(Tag("ContourData"), "DS", roi_coordinates)
        else:
            contour.add_new(Tag("ContourGeometricType"), "CS", "CLOSED_PLANAR")
            contour.add_new(Tag("NumberOfContourPoints"), "IS",
                            number_of_contour_points - 1)
            contour.add_new(Tag("ContourData"), "DS", roi_coordinates[0:-3])

    rtss.ROIContourSequence[position].ContourSequence.extend(contour_sequence)

    return rtss


def create_roi(rtss, roi_name, roi_coordinates, data_set,
               rt_roi_interpreted_type="ORGAN"):
    """
        Create new ROI to rtss

        :param rtss: dataset of RTSS
        :param roi_name: ROIName
        :param roi_coordinates: Coordinates of pixels for new ROI
        :param data_set: Data Set of selected DICOM image file
        :return: rtss, with added ROI
        """

    patient_dict_container = PatientDictContainer()
    existing_rois = patient_dict_container.get("rois")
    roi_exists = False

    # This is for adding a new slice to an already existing ROI.
    # For Future Development.
    # Check to see if the ROI already exists
    for key, value in existing_rois.items():
        if value["name"] == roi_name:
            roi_exists = True

    if not roi_exists:
        number_of_contour_points = len(roi_coordinates) / 3
        referenced_sop_class_uid = data_set.SOPClassUID
        referenced_sop_instance_uid = data_set.SOPInstanceUID
        if len(rtss.StructureSetROISequence) > 0:
            referenced_frame_of_reference_uid = rtss.StructureSetROISequence[-1].ReferencedFrameOfReferenceUID
            roi_number = rtss.StructureSetROISequence[-1].ROINumber + 1
        else:
            referenced_frame_of_reference_uid = rtss.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
            roi_number = 1

        # Colour TBC
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        rgb = [red, green, blue]

        # Saving a new StructureSetROISequence
        structure_set_sequence = Sequence([Dataset()])

        original_structure_set = rtss.StructureSetROISequence

        for structure_set in structure_set_sequence:
            structure_set.add_new(Tag("ROINumber"), 'IS', roi_number)
            structure_set.add_new(Tag("ReferencedFrameOfReferenceUID"), 'UI',
                                  referenced_frame_of_reference_uid)
            structure_set.add_new(Tag("ROIName"), 'LO', roi_name)
            structure_set.add_new(Tag("ROIGenerationAlgorithm"), 'CS', "")

        # Combine old and new structure set
        original_structure_set.extend(structure_set_sequence)
        rtss.add_new(Tag("StructureSetROISequence"), "SQ",
                     original_structure_set)

        # Saving a new ROIContourSequence, ContourSequence,
        # ContourImageSequence
        roi_contour_sequence = Sequence([Dataset()])
        contour_sequence = Sequence([Dataset()])
        contour_image_sequence = Sequence([Dataset()])

        # Original File
        original_roi_contour = rtss.ROIContourSequence

        # ROI Contour Sequence
        for roi_contour in roi_contour_sequence:
            roi_contour.add_new(Tag("ROIDisplayColor"), "IS", rgb)
            roi_contour.add_new(Tag("ContourSequence"), "SQ", contour_sequence)

            # ROI Sequence
            for contour in contour_sequence:
                # if data_set.get("ReferencedImageSequence"):
                contour.add_new(Tag("ContourImageSequence"), "SQ",
                                contour_image_sequence)

                # Contour Sequence
                for contour_image in contour_image_sequence:
                    contour_image.add_new(
                        Tag("ReferencedSOPClassUID"), "UI",
                        referenced_sop_class_uid)  # CT Image Storage
                    contour_image.add_new(Tag("ReferencedSOPInstanceUID"),
                                          "UI", referenced_sop_instance_uid)

                contour.add_new(Tag("ContourNumber"), "IS", 1)
                if not _is_closed_contour(roi_coordinates):
                    contour.add_new(Tag("ContourGeometricType"), "CS",
                                    "OPEN_PLANAR")
                    contour.add_new(Tag("NumberOfContourPoints"), "IS",
                                    number_of_contour_points)
                    contour.add_new(Tag("ContourData"), "DS", roi_coordinates)
                else:
                    contour.add_new(Tag("ContourGeometricType"), "CS",
                                    "CLOSED_PLANAR")
                    contour.add_new(Tag("NumberOfContourPoints"), "IS",
                                    number_of_contour_points - 1)
                    contour.add_new(Tag("ContourData"), "DS",
                                    roi_coordinates[0:-3])

            roi_contour.add_new(Tag("ReferencedROINumber"), "IS", roi_number)

        # Combine original ROIContourSequence with new
        original_roi_contour.extend(roi_contour_sequence)

        rtss.add_new(Tag("ROIContourSequence"), "SQ", original_roi_contour)

        # Saving a new RTROIObservationsSequence
        rt_roi_observations_sequence = Sequence([Dataset()])

        original_roi_observation_sequence = rtss.RTROIObservationsSequence

        for ROI_observations in rt_roi_observations_sequence:
            # TODO: Check to make sure that there aren't multiple observations
            #  per ROI, e.g. increment from existing Observation Numbers?
            ROI_observations.add_new(Tag("ObservationNumber"), 'IS',
                                     roi_number)
            ROI_observations.add_new(Tag("ReferencedROINumber"), 'IS',
                                     roi_number)
            ROI_observations.add_new(Tag("RTROIInterpretedType"), 'CS',
                                     rt_roi_interpreted_type)

        original_roi_observation_sequence.extend(rt_roi_observations_sequence)
        rtss.add_new(Tag("RTROIObservationsSequence"), "SQ",
                     original_roi_observation_sequence)

    else:
        # Add contour image data to existing ROI
        rtss = add_to_roi(rtss, roi_name, roi_coordinates, data_set)

    return rtss


def _within_tolerance(a: float, b: float, tol=0.01):
    return abs(a - b) < tol


def _is_closed_contour(roi_coordinates):
    if len(roi_coordinates) % 3 != 0:
        return False

    first_contour_point = roi_coordinates[:3]
    last_contour_point = roi_coordinates[-3:]
    closed = map(_within_tolerance, first_contour_point, last_contour_point)
    if False in closed:
        return False
    return True


def get_raw_contour_data(rtss):
    """
    Get raw contour data of ROI in RT Structure Set

    :param rtss: RTSS dataset
    :return: dict_roi, a dictionary of ROI contours; dict_num_points, number of
    points of contours.
    """
    # Retrieve a dictionary of roi_name & ROINumber pairs
    dict_id = {}
    for i, elem in enumerate(rtss.StructureSetROISequence):
        roi_number = elem.ROINumber
        roi_name = elem.ROIName
        dict_id[roi_number] = roi_name

    dict_roi = {}
    dict_num_points = {}
    for roi in rtss.ROIContourSequence:
        referenced_roi_number = roi.ReferencedROINumber
        roi_name = dict_id[referenced_roi_number]
        dict_contour = collections.defaultdict(list)
        roi_points_count = 0
        for roi_slice in roi.ContourSequence:
            for contour_img in roi_slice.ContourImageSequence:
                referenced_sop_instance_uid = \
                    contour_img.ReferencedSOPInstanceUID
            contour_geometric_type = roi_slice.ContourGeometricType
            number_of_contour_points = roi_slice.NumberOfContourPoints
            roi_points_count += int(number_of_contour_points)
            contour_data = roi_slice.ContourData
            dict_contour[referenced_sop_instance_uid].append(contour_data)
        dict_roi[roi_name] = dict_contour
        dict_num_points[roi_name] = roi_points_count
    return dict_roi, dict_num_points


def calculate_matrix(img_ds):
    """
    Calculate the transformation matrix of a DICOM(image) dataset.

    :param img_ds: DICOM(image) dataset
    :return: pair of numpy arrays that represents the transformation matrix
    """
    # Physical distance (in mm) between the center of each image pixel,
    # specified by a numeric pair
    # - adjacent row spacing (delimiter) adjacent column spacing.
    dist_row = img_ds.PixelSpacing[0]
    dist_col = img_ds.PixelSpacing[1]
    # The direction cosines of the first row and the first column with
    # respect to the patient.
    # 6 values inside: [Xx, Xy, Xz, Yx, Yy, Yz]
    orientation = img_ds.ImageOrientationPatient
    # The x, y, and z coordinates of the upper left hand corner
    # (center of the first voxel transmitted) of the image, in mm.
    # 3 values: [Sx, Sy, Sz]
    position = img_ds.ImagePositionPatient

    # Equation C.7.6.2.1-1.
    # https://dicom.innolitics.com/ciods/rt-structure-set/roi-contour/30060039/30060040/30060050
    matrix_m = np.ndarray(
        shape=(4, 4),
        buffer=np.array(
            [
                [orientation[0] * dist_row, orientation[3] * dist_col, 0,
                 position[0]],
                [orientation[1] * dist_row, orientation[4] * dist_col, 0,
                 position[1]],
                [orientation[2] * dist_row, orientation[5] * dist_col, 0,
                 position[2]],
                [0, 0, 0, 1],
            ],
            dtype=float,
        ),
    )

    x = []
    y = []
    for i in range(0, img_ds.Columns):
        i_mat = np.matmul(
            matrix_m,
            np.ndarray(
                shape=(4, 1),
                buffer=np.array([[i], [0], [0], [1]], dtype=float)
            ),
        )
        x.append(float(i_mat[0]))

    for j in range(0, img_ds.Rows):
        j_mat = np.matmul(
            matrix_m,
            np.ndarray(
                shape=(4, 1),
                buffer=np.array([[0], [j], [0], [1]], dtype=float)
            ),
        )
        y.append(float(j_mat[1]))

    return np.array(x), np.array(y)


def get_pixluts(dict_ds):
    """
    Calculate transformation matrices for all the slices.

    :param dict_ds: a dictionary of all the datasets
    :return: a dictionary of transformation matrices
    """
    dict_pixluts = {}
    non_img_type = ["rtdose", "rtplan", "rtss"]
    for ds in dict_ds:
        if ds not in non_img_type:
            img_ds = dict_ds[ds]
            pixlut = calculate_matrix(img_ds)
            dict_pixluts[img_ds.SOPInstanceUID] = pixlut
    return dict_pixluts


def calculate_pixels(pixlut, contour, prone=False, feetfirst=False):
    """
    Calculate (Convert) contour points.

    :param pixlut: transformation matrixx
    :param contour: raw contour data (3D)
    :param prone: label of prone
    :param feetfirst: label of feetfirst or head first
    :return: contour pixels
    """
    pixels = []

    np_x = np.array(pixlut[0])
    np_y = np.array(pixlut[1])
    if not feetfirst and not prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmax(np_x > con_x)
            y = np.argmax(np_y > con_y)
            pixels.append([x, y])
    if feetfirst and not prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmin(np_x < con_x)
            y = np.argmax(np_y > con_y)
            pixels.append([x, y])
    if prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmin(np_x < con_x)
            y = np.argmin(np_y < con_y)
            pixels.append([x, y])

    return pixels


def calculate_pixels_sagittal(pixlut, contour, prone=False, feetfirst=False):
    """
    Calculate (Convert) contour points.

    :param pixlut: transformation matrixx
    :param contour: raw contour data (3D)
    :param prone: label of prone
    :param feetfirst: label of feetfirst or head first
    :return: contour pixels

    Parameters
    ----------
    contour : object
    """
    pixels = []
    np_x = np.array(pixlut[0])
    np_y = np.array(pixlut[1])
    if not feetfirst and not prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmax(np_x > con_x)
            y = np.argmax(np_y > con_y)
            pixels.append([x, y])
    if feetfirst and not prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmin(np_x < con_x)
            y = np.argmax(np_y > con_y)
            pixels.append([x, y])
    if prone:
        for i in range(0, len(contour), 3):
            con_x = contour[i]
            con_y = contour[i + 1]
            x = np.argmin(np_x < con_x)
            y = np.argmin(np_y < con_y)
            pixels.append([x, y])
    return pixels


def pixel_to_rcs(pixlut, x, y):
    """
    :param pixlut: Transformation matrix
    :param x: Pixel X value (greater than 0, less than the slice's Columns
    data element)
    :param y: Pixel Y value (greater than 0, less than the slice's Rows data
    element)
    :return: The pixel coordinate converted to an RCS point as set by the
    image slice.
    """

    np_x = np.array(pixlut[0])
    np_y = np.array(pixlut[1])

    x_on_pixlut = np_x[x - 1]
    y_on_pixlut = np_y[y - 1]

    return x_on_pixlut, y_on_pixlut


def get_contour_pixel(
        dict_raw_contour_data,
        roi_selected,
        dict_pixluts,
        curr_slice,
        prone=False,
        feetfirst=False,
):
    """
    Get pixels of contours of all rois selected within current slice.
    {slice: list of pixels of all contours in this slice}

    :param dict_raw_contour_data: a dictionary of all raw contour data
    :param roi_selected: a list of currently selected ROIs
    :param dict_pixluts: a dictionary of transformation matrices
    :param curr_slice: Current slice identifier
    :param prone: label of prone
    :param feetfirst: label of feetfirst or head first
    :return: a dictionary of contour pixels
    """
    dict_pixels = {}
    pixlut = dict_pixluts[curr_slice]
    for roi in roi_selected:
        # Using this type of dict to handle multiple contours within one slice
        dict_pixels_of_roi = collections.defaultdict(list)
        raw_contours = dict_raw_contour_data[roi]
        number_of_contours = len(raw_contours[curr_slice])
        for i in range(number_of_contours):
            contour_pixels = calculate_pixels(
                pixlut, raw_contours[curr_slice][i], prone, feetfirst
            )
            dict_pixels_of_roi[curr_slice].append(contour_pixels)
        dict_pixels[roi] = dict_pixels_of_roi

    return dict_pixels


def get_roi_contour_pixel(dict_raw_contour_data, roi_list, dict_pixluts):
    """
    Get pixels of contours of all rois at one time. (Alternative method for
    calculating ROIs.

    :param dict_raw_contour_data: a dictionary of all raw contour data
    :param roi_list: a list of all existing ROIs
    :param dict_pixluts: a dictionary of transformation matrices
    :return: a dictionary of contour pixels of all ROIs
    """
    dict_pixels = {}
    for roi in roi_list:
        dict_pixels_of_roi = collections.defaultdict(list)
        raw_contour = dict_raw_contour_data[roi]
        for roi_slice in raw_contour:
            pixlut = dict_pixluts[roi_slice]
            number_of_contours = len(raw_contour[roi_slice])
            for i in range(number_of_contours):
                contour_pixels = calculate_pixels(pixlut,
                                                  raw_contour[roi_slice][i])
                dict_pixels_of_roi[roi_slice].append(contour_pixels)
        dict_pixels[roi] = dict_pixels_of_roi
    return dict_pixels


def transform_rois_contours(axial_rois_contours):
    """
       Transform the axial ROI contours into coronal and sagittal contours
       :param axial_rois_contours: the dictionary of axial ROI contours
       :return: Tuple of coronal and sagittal ROI contours
    """
    coronal_rois_contours = {}
    sagittal_rois_contours = {}
    slice_ids = dict((v, k) for k, v in PatientDictContainer().get("dict_uid").items())
    for name in axial_rois_contours.keys():
        coronal_rois_contours[name] = {}
        sagittal_rois_contours[name] = {}
        for slice_id in slice_ids:
            contours = axial_rois_contours[name][slice_id]
            for contour in contours:
                for i in range(len(contour)):
                    if contour[i][1] in coronal_rois_contours[name]:
                        coronal_rois_contours[name][contour[i][1]][0].append([contour[i][0], slice_ids[slice_id]])
                    else:
                        coronal_rois_contours[name][contour[i][1]] = [[]]
                        coronal_rois_contours[name][contour[i][1]][0].append([contour[i][0], slice_ids[slice_id]])

                    if contour[i][0] in sagittal_rois_contours[name]:
                        sagittal_rois_contours[name][contour[i][0]][0].append([contour[i][1], slice_ids[slice_id]])
                    else:
                        sagittal_rois_contours[name][contour[i][0]] = [[]]
                        sagittal_rois_contours[name][contour[i][0]][0].append([contour[i][1], slice_ids[slice_id]])
    return coronal_rois_contours, sagittal_rois_contours


def calc_roi_polygon(curr_roi, curr_slice, dict_rois_contours, pixmap_aspect=1):
    """
    Calculate a list of polygons to display for a given ROI and a given slice.

    :param curr_roi: the ROI structure
    :param curr_slice: the current slice
    :param dict_rois_contours: the dictionary of ROI contours
    :param pixmap_aspect: the scaling ratio
    :return: List of polygons of type QPolygonF.
    """
    # TODO Implement support for showing "holes" in contours.
    # Possible process for this is:
    # 1. Calculate the areas of each contour on the slice
    # https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
    # 2. Compare each contour to the largest contour by area to determine if it is contained entirely within the
    # largest contour.
    # https://stackoverflow.com/questions/4833802/check-if-polygon-is-inside-a-polygon
    # 3. If the polygon is contained, use QPolygonF.subtracted(QPolygonF) to subtract the smaller "hole" polygon
    # from the largest polygon, and then remove the polygon from the list of polygons to be displayed.
    # This process should provide fast and reliable results, however it should be noted that this method may fall
    # apart in a situation where there are multiple "large" polygons, each with their own hole in it. An appropriate
    # solution to that may be to compare every contour against one another and determine which ones have holes
    # encompassed entirely by them, and then subtract each hole from the larger polygon and delete the smaller
    # holes. This second solution would definitely lead to more accurate representation of contours, but could
    # possibly be too slow to be viable.

    if curr_slice not in dict_rois_contours[curr_roi]:
        return []

    list_polygons = []
    pixel_list = dict_rois_contours[curr_roi][curr_slice]
    for i in range(len(pixel_list)):
        list_qpoints = []
        contour = pixel_list[i]
        for point in contour:
            curr_qpoint = QtCore.QPoint(point[0], point[1] * pixmap_aspect)
            list_qpoints.append(curr_qpoint)
        curr_polygon = QtGui.QPolygonF(list_qpoints)
        list_polygons.append(curr_polygon)
    return list_polygons


def ordered_list_rois(rois):
    res = []
    for roi_id, value in rois.items():
        res.append(roi_id)
    return sorted(res)


def create_initial_rtss_from_ct(img_ds: pydicom.dataset.Dataset, filepath: Path,
                                ct_uid_list=[]) -> pydicom.dataset.FileDataset:
    """Pre-populate an RT Structure Set based on a single CT (or MR) and a
    list of image UIDs The caller should update the Structure Set Label,
    Name, and Description, which are set to "OnkoDICOM" plus the StudyID
    from the CT, and must add Structure Set ROI Sequence, ROI Contour
    Sequence, and RT ROI Observations Sequence

    Parameters
    ----------
    img_ds : pydicom.dataset.Dataset
        A CT or MR image that the RT Structure Set will be "drawn" on
    ct_uid_list : list, optional
        list of UIDs (as strings) of the entire image volume that the RT SS
        references, by default []
    filepath: str
        A path where the RTStruct will be saved

    Returns
    -------
    pydicom.dataset.FileDataset
        the half-baked RT SS, ready for Structure Set ROI Sequence,
        ROI Contour Sequence, and RT ROI Observations Sequence

    Raises
    ------
    ValueError
        [description]
    """
    if img_ds is None:
        raise ValueError("No CT data to initialize RT SS")

    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")

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

    # File meta
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 238
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
    file_meta.MediaStorageSOPInstanceUID = '1.2.3.4'
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    validate_file_meta(file_meta)

    rt_ss = pydicom.dataset.FileDataset(filepath, {}, preamble=b"\0" * 128, file_meta=file_meta)
    rt_ss.fix_meta_info()

    for tag in top_level_tags_to_copy:
        if tag in img_ds:
            rt_ss[tag] = deepcopy(img_ds[tag])

    # Best to modify the Structure Set Label with something more interesting
    # in the application. and populate the Name and Description from the
    # application also.
    rt_ss.StructureSetLabel = "OnkoDICOM rtss of " + rt_ss.StudyID
    rt_ss.StructureSetName = rt_ss.StructureSetLabel
    rt_ss.StructureSetDescription = rt_ss.StructureSetLabel

    # General Equipment Module
    rt_ss.Manufacturer = "OnkoDICOM"
    rt_ss.ManufacturersModelName = "OnkoDICOM"
    # TODO: Pull this off build information in some way
    rt_ss.SoftwareVersions = "2021"

    # RT Series Module
    rt_ss.SeriesInstanceUID = pydicom.uid.generate_uid()
    rt_ss.Modality = "RTSTRUCT"
    rt_ss.SeriesDate = dicom_date
    rt_ss.SeriesTime = dicom_time
    rt_ss.SeriesNumber = 1

    # RT Referenced Frame Of Reference Sequence, Structure Set Module
    rt_ref_frame_of_ref_sequence_item = pydicom.dataset.Dataset()
    rt_ref_frame_of_ref_sequence_item.FrameOfReferenceUID = img_ds.FrameOfReferenceUID
    rt_ss.ReferencedFrameOfReferenceSequence = [rt_ref_frame_of_ref_sequence_item]

    rt_ref_study_sequence_item = pydicom.dataset.Dataset()
    rt_ref_study_sequence_item.ReferencedSOPInstanceUID = img_ds.StudyInstanceUID
    rt_ref_study_sequence_item.ReferencedSOPClassUID = img_ds.SOPClassUID

    rt_ref_series_sequence_item = pydicom.dataset.Dataset()
    rt_ref_series_sequence_item.SeriesInstanceUID = img_ds.SeriesInstanceUID

    contour_image_sequence = []
    referenced_image_sequence = []
    for uid in ct_uid_list:
        contour_image_sequence_item = pydicom.dataset.Dataset()
        referenced_image_sequence_item = pydicom.dataset.Dataset()
        referenced_image_sequence_item.ReferencedSOPClassUID = img_ds.SOPClassUID
        contour_image_sequence_item.ReferencedSOPClassUID = img_ds.SOPClassUID
        referenced_image_sequence_item.ReferencedSOPInstanceUID = uid
        contour_image_sequence_item.ReferencedSOPInstanceUID = uid
        contour_image_sequence.append(contour_image_sequence_item)
        referenced_image_sequence.append(referenced_image_sequence_item)

    rt_ref_frame_of_ref_sequence_item.ContourImageSequence = contour_image_sequence
    rt_ss.ReferencedImageSequence = referenced_image_sequence

    referenced_series_sequence_item = pydicom.dataset.Dataset()
    referenced_series_sequence_item.SeriesInstanceUID = img_ds.SeriesInstanceUID
    # acceptable to copy because the contents of each reference sequence
    # item only include SOP Class and SOP Instance, and not additional
    # elements that are in referenced image seq but not referenced instance
    # seq
    referenced_series_sequence_item.ReferencedInstanceSequence = shallowcopy(referenced_image_sequence)
    rt_ss.ReferencedSeriesSequence = [referenced_series_sequence_item]
    rt_ref_study_sequence_item.RTReferencedSeriesSequence = [rt_ref_series_sequence_item]
    rt_ref_frame_of_ref_sequence_item.RTReferencedStudySequence = [rt_ref_study_sequence_item]

    rt_ss.StructureSetROISequence = []
    rt_ss.ROIContourSequence = []
    rt_ss.RTROIObservationsSequence = []
    rt_ss.SOPClassUID = "1.2.840.10008.5.1.4.1.1.481.3"
    rt_ss.SOPInstanceUID = pydicom.uid.generate_uid()

    rt_ss.InstanceCreationDate = rt_ss.StructureSetDate = dicom_date

    rt_ss.InstanceCreationTime = rt_ss.StructureSetTime = dicom_time
    rt_ss.is_little_endian = True
    rt_ss.is_implicit_VR = True
    return rt_ss
