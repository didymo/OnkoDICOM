import collections
import pydicom
from pydicom import Sequence, Dataset
from pydicom.tag import Tag

from src.Model.CalculateImages import *
from src.Model.PatientDictContainer import PatientDictContainer


def rename_roi(rtss, roi_id, new_name):
    """
    Renames the given Region of Interest. Creates a csv file storing all the renamed ROIs for the given RTSTRUCT file.
    :param rtss: The RTSTRUCT file.
    :param roi_id: ID the structure produced by ImageLoading.get_rois(..)
    :param new_name: The structure's new name
    """
    for sequence in rtss.StructureSetROISequence:
        if sequence.ROINumber == roi_id:
            sequence.ROIName = new_name

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


def create_roi(rtss, roi_name, roi_coordinates, data_set):

    referenced_sop_class_uid = data_set.ReferencedImageSequence[0].ReferencedSOPClassUID
    referenced_sop_instance_uid = data_set.ReferencedImageSequence[0].ReferencedSOPInstanceUID

    referenced_frame_of_reference_uid = rtss["StructureSetROISequence"].value[0].ReferencedFrameOfReferenceUID
    roi_number = rtss["StructureSetROISequence"].value[-1].ROINumber+1
    rgb = [10, 50, 100]  # Colour TBC

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
    rtss.add_new(Tag("StructureSetROISequence"), "SQ", original_structure_set)

    # Saving a new ROIContourSequence, ContourSequence, ContourImageSequence
    roi_contour_sequence = Sequence([Dataset()])
    contour_sequence = Sequence([Dataset()])
    contour_image_sequence = Sequence([Dataset()])

    # Original File
    original_ROI_contour = rtss.ROIContourSequence

    # ROI Contour Sequence
    for roi_contour in roi_contour_sequence:
        roi_contour.add_new(Tag("ROIDisplayColor"), "IS", rgb)
        roi_contour.add_new(Tag("ContourSequence"), "SQ", contour_sequence)

        # ROI Sequence
        for contour in contour_sequence:
            contour.add_new(Tag("ContourImageSequence"), "SQ", contour_image_sequence)

            # Contour Sequence
            for contour_image in contour_image_sequence:
                contour_image.add_new(Tag("ReferencedSOPClassUID"), "UI", referenced_sop_class_uid)  # CT Image Storage
                contour_image.add_new(Tag("ReferencedSOPInstanceUID"), "UI", referenced_sop_instance_uid) #Placeholder

            contour.add_new(Tag("ContourGeometricType"), "CS", "CLOSED_PLANAR")
            contour.add_new(Tag("NumberOfContourPoints"), "IS", 10)
            contour.add_new(Tag("ContourNumber"), "IS", 5)
            contour.add_new(Tag("ContourData"), "DS", roi_coordinates)

        roi_contour.add_new(Tag("ReferencedROINumber"), "IS", roi_number)

    # Combine original ROIContourSequence with new
    original_ROI_contour.extend(roi_contour_sequence)

    rtss.add_new(Tag("ROIContourSequence"), "SQ", original_ROI_contour)

    # Saving a new RTROIObservationsSequence
    RT_ROI_observations_sequence = Sequence([Dataset()])

    original_ROI_observation_sequence = rtss.RTROIObservationsSequence

    for ROI_observations in RT_ROI_observations_sequence:
        ROI_observations.add_new(Tag("ObservationNumber"), 'IS', roi_number)
        ROI_observations.add_new(Tag("ReferencedROINumber"), 'IS', roi_number)
        ROI_observations.add_new(Tag("RTROIInterpretedType"), 'CS', "")

    original_ROI_observation_sequence.extend(RT_ROI_observations_sequence)
    rtss.add_new(Tag("RTROIObservationsSequence"), "SQ", original_ROI_observation_sequence)

    print(rtss)
    patient_dict_container = PatientDictContainer()
    rtss_location = patient_dict_container.filepaths["rtss"]

    # To save
    pydicom.filewriter.dcmwrite(rtss_location, rtss, write_like_original=True)


def get_raw_contour_data(rtss):
    """
    Get raw contour data of ROI in RT Structure Set

    :param rtss: RTSS dataset
    :return: dict_ROI, a dictionary of ROI contours; dict_NumPoints, number of points of contours.
    """
    # Retrieve a dictionary of ROIName & ROINumber pairs
    dict_id = {}
    for i, elem in enumerate(rtss.StructureSetROISequence):
        roi_number = elem.ROINumber
        roi_name = elem.ROIName
        dict_id[roi_number] = roi_name

    dict_ROI = {}
    dict_NumPoints = {}
    for roi in rtss.ROIContourSequence:
        ROIDisplayColor = roi.ROIDisplayColor
        ReferencedROINumber = roi.ReferencedROINumber
        ROIName = dict_id[ReferencedROINumber]
        dict_contour = collections.defaultdict(list)
        roi_points_count = 0
        for slice in roi.ContourSequence:
            for contour_img in slice.ContourImageSequence:
                ReferencedSOPInstanceUID = contour_img.ReferencedSOPInstanceUID
            ContourGeometricType = slice.ContourGeometricType
            NumberOfContourPoints = slice.NumberOfContourPoints
            roi_points_count += int(NumberOfContourPoints)
            ContourData = slice.ContourData
            dict_contour[ReferencedSOPInstanceUID].append(ContourData)
        dict_ROI[ROIName] = dict_contour
        dict_NumPoints[ROIName] = roi_points_count
    return dict_ROI, dict_NumPoints


def calculate_matrix(img_ds):
    """
    Calculate the transformation matrix of a DICOM(image) dataset.

    :param img_ds: DICOM(image) dataset
    :return: pair of numpy arrays that represents the transformation matrix
    """
    # Physical distance (in mm) between the center of each image pixel, specified by a numeric pair
    # - adjacent row spacing (delimiter) adjacent column spacing.
    dist_row = img_ds.PixelSpacing[0]
    dist_col = img_ds.PixelSpacing[1]
    # The direction cosines of the first row and the first column with respect to the patient.
    # 6 values inside: [Xx, Xy, Xz, Yx, Yy, Yz]
    orientation = img_ds.ImageOrientationPatient
    # The x, y, and z coordinates of the upper left hand corner
    # (center of the first voxel transmitted) of the image, in mm.
    # 3 values: [Sx, Sy, Sz]
    position = img_ds.ImagePositionPatient

    # Equation C.7.6.2.1-1.
    # https://dicom.innolitics.com/ciods/rt-structure-set/roi-contour/30060039/30060040/30060050
    matrix_M = np.ndarray(
        shape=(4, 4),
        buffer=np.array(
            [
                [orientation[0] * dist_row, orientation[3] * dist_col, 0, position[0]],
                [orientation[1] * dist_row, orientation[4] * dist_col, 0, position[1]],
                [orientation[2] * dist_row, orientation[5] * dist_col, 0, position[2]],
                [0, 0, 0, 1],
            ],
            dtype=np.float,
        ),
    )

    x = []
    y = []
    for i in range(0, img_ds.Columns):
        i_mat = np.matmul(
            matrix_M,
            np.ndarray(
                shape=(4, 1), buffer=np.array([[i], [0], [0], [1]], dtype=np.float)
            ),
        )
        x.append(float(i_mat[0]))

    for j in range(0, img_ds.Rows):
        j_mat = np.matmul(
            matrix_M,
            np.ndarray(
                shape=(4, 1), buffer=np.array([[0], [j], [0], [1]], dtype=np.float)
            ),
        )
        y.append(float(j_mat[1]))

    return (np.array(x), np.array(y))


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

    ## Optimization 1: Reduce unnecessary IF STATEMENTS
    ## Time used: 488.194700717926
    # if (not prone and not feetfirst):
    #     for i in range(0, len(contour), 3):
    #         for x, x_val in enumerate(pixlut[0]):
    #             if x_val > contour[i]:
    #                 break
    #         for y, y_val in enumerate(pixlut[1]):
    #             if y_val > contour[i+1]:
    #                 break
    #         pixels.append([x, y])

    ### Optimization 2: Using Numpy Matrix
    ### Time used: 5.099231481552124
    # np_x = np.array(pixlut[0])
    # np_y = np.array(pixlut[1])
    # for i in range(0, len(contour), 3):
    #     con_x = contour[i]
    #     con_y = contour[i+1]
    #     x = np.argmax(np_x > con_x)
    #     y = np.argmax(np_y > con_y)
    #     pixels.append([x, y])

    ### Opitimazation 1 & 2
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

    ### Original Slowwwwwwww One
    ### Time used: 895.787469625473
    # for i in range(0, len(contour), 3):
    #     for x, x_val in enumerate(pixlut[0]):
    #         if (x_val > contour[i] and not prone and not feetfirst):
    #             break
    #         elif (x_val < contour[i]):
    #             if feetfirst or prone:
    #                 break
    #     for y, y_val in enumerate(pixlut[1]):
    #         if (y_val > contour[i + 1] and not prone):
    #             break
    #         elif (y_val < contour[i + 1] and prone):
    #             break
    #     pixels.append([x, y])
    return pixels


def get_contour_pixel(
        dict_raw_ContourData,
        roi_selected,
        dict_pixluts,
        curr_slice,
        prone=False,
        feetfirst=False,
):
    """
    Get pixels of contours of all rois selected within current slice.
    {slice: list of pixels of all contours in this slice}

    :param dict_raw_ContourData: a dictionary of all raw contour data
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
        raw_contours = dict_raw_ContourData[roi]
        number_of_contours = len(raw_contours[curr_slice])
        for i in range(number_of_contours):
            contour_pixels = calculate_pixels(
                pixlut, raw_contours[curr_slice][i], prone, feetfirst
            )
            dict_pixels_of_roi[curr_slice].append(contour_pixels)
        dict_pixels[roi] = dict_pixels_of_roi

    return dict_pixels


def get_roi_contour_pixel(dict_raw_ContourData, roi_list, dict_pixluts):
    """
    Get pixels of contours of all rois at one time. (Alternative method for calculating ROIs.

    :param dict_raw_ContourData: a dictionary of all raw contour data
    :param roi_list: a list of all existing ROIs
    :param dict_pixluts: a dictionary of transformation matrices
    :return: a dictionary of contour pixels of all ROIs
    """
    dict_pixels = {}
    for roi in roi_list:
        dict_pixels_of_roi = collections.defaultdict(list)
        raw_contour = dict_raw_ContourData[roi]
        for slice in raw_contour:
            pixlut = dict_pixluts[slice]
            number_of_contours = len(raw_contour[slice])
            for i in range(number_of_contours):
                contour_pixels = calculate_pixels(pixlut, raw_contour[slice][i])
                dict_pixels_of_roi[slice].append(contour_pixels)
        dict_pixels[roi] = dict_pixels_of_roi
    return dict_pixels


def ordered_list_rois(rois):
    res = []
    for id, value in rois.items():
        res.append(id)
    return sorted(res)
