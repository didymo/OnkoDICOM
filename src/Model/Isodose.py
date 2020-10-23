""" Contains functions required for isodose display """

import numpy as np
from src.Model.ROI import calculate_matrix


def get_dose_pixels(pixlut, doselut, img_ds):
    """Convert dosegrid into pixel values"""

    x = []
    y = []

    # PatientPosition: Describes patient position relative to the equipment
    # Check if patient prone
    if 'p' in img_ds.PatientPosition.lower():
        prone = -1  # Prone
    else:
        prone = 1  # Supine

    # Check if patient feetfirst
    if 'ff' in img_ds.PatientPosition.lower():
        feetfirst = -1  # Feet first
    else:
        feetfirst = 1  # Head first

    # Physical distance (in mm) between the center of each image pixel
    spacing = img_ds.PixelSpacing

    # Formula based on GetDoseGridPixelData function in dicompyler
    # (https://github.com/bastula/dicompyler/blob/master/dicompyler/baseplugins/2dview.py)
    x = (np.array(doselut[0]) - pixlut[0][0]) * \
        prone * feetfirst / spacing[0]
    y = (np.array(doselut[1]) - pixlut[1][0]) * prone / spacing[1]

    return (x, y)


def get_dose_pixluts(dict_ds):
    """Convert dosegrid data for each slice into pixel values

    :param dict_ds:     dictionary containing patient data
    :return:            dictionary with dose pixel values as values and
                        SOPInstanceUID as key
    """

    dict_dose_pixluts = {}
    dict_dose_pixluts = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss', 'rtimage']
    dose_data = calculate_matrix(dict_ds['rtdose'])
    for ds in dict_ds:
        if ds not in non_img_type:
            img_ds = dict_ds[ds]
            pixlut = calculate_matrix(img_ds)
            dose_pixlut = get_dose_pixels(pixlut, dose_data, img_ds)
            dict_dose_pixluts[img_ds.SOPInstanceUID] = dose_pixlut
    return dict_dose_pixluts


def get_dose_grid(rtd, z=0):
    """
    Return the 2d dose grid for the given slice position (mm). 
    Based on the function GetDoseGrid in dicompyler-core
    (https://github.com/dicompyler/dicompyler-core/blob/master/dicompylercore/dicomparser.py)

    :param rtd:     Data from RTDose file
    :param z:       Position of slice in mm
    :return:        Dose grid as a 2d numpy array
    """

    if 'GridFrameOffsetVector' in rtd:
        z = float(z)

        planes = rtd.ImageOrientationPatient[0] * np.array(rtd.GridFrameOffsetVector) + \
            rtd.ImagePositionPatient[2]
        frame = -1

        if (np.amin(np.fabs(planes - z)) < 0.5):
            frame = np.argmin(np.fabs(planes - z))
            return rtd.pixel_array[frame]

        if ((z > np.amin(planes)) or (z < np.amax(planes))):
            umin = np.fabs(planes - z)
            lmin = umin.copy()
            ub = np.argmin(umin)

            lmin[ub] = np.amax(umin)
            lb = np.argmin(lmin)

            # Fractional distance from bottom to top
            # Plane is at upper plane if 1, lower plane if 0
            fz = (z - planes[lb]) / (planes[ub] - planes[lb])

            plane = fz * rtd.pixel_array[ub] + \
                (1.0 - fz) * rtd.pixel_array[lb]

            return plane

        return np.array([])


def calculate_rxdose(rtplan):
    rxdose = 1
    if ('DoseReferenceSequence' in rtplan and
            rtplan.DoseReferenceSequence[0].DoseReferenceStructureType and
            rtplan.DoseReferenceSequence[0].TargetPrescriptionDose):
        rxdose = rtplan.DoseReferenceSequence[0].TargetPrescriptionDose * 100
    # beam doses are to a point, not necessarily to the same point
    # and don't necessarily add up to the prescribed dose to the target
    # which is frequently to a SITE rather than to a POINT
    elif rtplan.FractionGroupSequence:
        fraction_group = rtplan.FractionGroupSequence[0]
        if ("NumberOfFractionsPlanned" in fraction_group) and \
                ("ReferencedBeamSequence" in fraction_group):
            beams = fraction_group.ReferencedBeamSequence
            number_of_fractions = fraction_group.NumberOfFractionsPlanned
            for beam in beams:
                if "BeamDose" in beam:
                    rxdose += beam.BeamDose * number_of_fractions * 100

    return rxdose
