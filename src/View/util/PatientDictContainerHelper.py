import SimpleITK as sitk


def get_dict_slice_to_uid(patient_dict_container):
    """
    This function swap the keys and values in
    dict_uid from patient dict container to create new dictionary for
    slice lookup.
    """
    return dict(
        (v, k) for k, v in patient_dict_container.get("dict_uid").items())


def read_dicom_image_to_sitk(filepaths):
    """
    this function reads dicom image to sitk object
    :param filepaths: dictionary of filepaths in a dict container

    Returns: sitk object from filepaths
    """
    amount = len(filepaths)
    image_filepath_list = []

    for i in range(amount):
        try:
            image_filepath_list.append(filepaths[i])
        except KeyError:
            continue

    return sitk.ReadImage(image_filepath_list)
