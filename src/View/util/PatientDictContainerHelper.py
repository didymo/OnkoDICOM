def get_dict_slice_to_uid(patient_dict_container):
    return dict(
        (v, k) for k, v in patient_dict_container.get("dict_uid").items())
