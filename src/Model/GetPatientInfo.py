import collections

import pydicom


def get_tree(ds, label=0):
    """
    Get a structured tree of patient, DICOM Tree

    :param ds: A dataset of the patient.
    :param label:
    :return: tree, a list with hierarchical information of the dataset
    """
    tree = []
    dont_print = ['Pixel Data', 'File Meta Information Version']
    # For all the elements in the dataset
    for elem in ds:
        curr_row = []
        # If it is a 'sequence'
        if elem.VR == "SQ":
            # Has Child?
            curr_row.append(label)
            curr_row.append(repr(elem.name))
            curr_row.append("")
            curr_row.append(repr(elem.tag))
            curr_row.append(repr(elem.VM))
            curr_row.append(repr(elem.VR))

            # Append to the return list
            tree.append(curr_row)
            # Recursive
            for seq_item in elem.value:
                items = get_tree(seq_item, 1)
            for item in items:
                tree.append(item)
        else:
            # Exclude pixel data and version info
            if elem.name not in dont_print:
                curr_row.append(label)
                curr_row.append(repr(elem.name))
                curr_row.append(repr(elem.value))
                curr_row.append(repr(elem.tag))
                curr_row.append(repr(elem.VM))
                curr_row.append(repr(elem.VR))
                # Append to the return list
                tree.append(curr_row)
    return tree


def get_basic_info(ds):
    """
    Get patient name, ID, gender and DOB

    :param ds: a dataset
    :return: dict_basic_info, a dictionary of PatientName, PatientID,
    PatientSex, PatientBirthDate.
    """
    dict_basic_info = {}
    dict_basic_info['name'] = str(ds.get("PatientName"))
    dict_basic_info['id'] = str(ds.get("PatientID"))
    dict_basic_info['gender'] = str(ds.get("PatientSex"))
    dict_basic_info['dob'] = str(ds.get("PatientBirthDate"))
    return dict_basic_info


def dict_instance_uid(dict_ds):
    """
    Get a dictionary where key = index of the slice and value is the Instance
    UID

    :param dict_ds:
    :return:
    """
    res = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss', 'rtimage']

    for ds in dict_ds:
        if ds not in non_img_type:
            if isinstance(ds, str):
                if ds[0:3] != 'sr-':
                    index = int(ds)
                    img_ds = dict_ds[ds]
                    res[index] = img_ds.SOPInstanceUID
            else:
                index = int(ds)
                img_ds = dict_ds[ds]
                res[index] = img_ds.SOPInstanceUID

    return res


# =========   This is a class for DICOM TREE   ===============
class DicomTree(object):
    """
    A class of DICOM tree
    """
    def __init__(self, filename):
        """
        DICOM Tree class constructor.

        :param filename: dicom file path
        """
        self.filename = filename
        if self.filename is not None:
            self.dataset = self.read_dcm(filename)
            self.dict = self.dataset_to_dict(self.dataset)

    def read_dcm(self, filename):
        """
        Read dicom file to dataset

        :param filename: dicom file path
        :return: dataset, dataset of the dicom file
        """
        dataset = pydicom.dcmread(filename, force=True)
        return dataset

    def data_element_to_dict(self, data_element):
        """
        Convert the data_element to an ordered dicitonary

        :param data_element: element level variable
        :return: dictionary
        """
        # Create an oredered dictionary
        ordered_dict = collections.OrderedDict()
        # If current data element is a sequence
        if data_element.VR == 'SQ':
            # Create an ordered dictionary for the items in the sequence.
            items = collections.OrderedDict()
            # Key: element name, Value: item
            ordered_dict[data_element.name] = items
            # Temporary value for indexing
            tmp = 0
            # For every items in the sequence element
            for dataset_item in data_element:
                # Convert the item to dictionary
                # And store it as key: 'item: index num',
                # value: dictionary of the item
                # in the dictionary
                items['item ' + str(tmp)] = self.dataset_to_dict(dataset_item)
                tmp += 1
        # If current data element is not pixel data element
        elif data_element.name != 'Pixel Data':
            # Key: name, value: value of the element
            temp_list = []
            temp_list.append(data_element.value)
            temp_list.append(repr(data_element.tag))
            temp_list.append(data_element.VM)
            temp_list.append(data_element.VR)
            ordered_dict[data_element.name] = temp_list
        return ordered_dict

    def dataset_to_dict(self, dataset):
        """
        Convert the dataset to an ordered dictionary.

        :param dataset: dicom dataset
        :return: dictionary
        """
        # Create an ordered dictionary
        ordered_dict = collections.OrderedDict()
        # For each element in the dataset
        for data_element in dataset:
            # Update the dictionary with the key/value pairs from dictionary.
            # The dictionary is converted from every data_element.
            ordered_dict.update(self.data_element_to_dict(data_element))
        return ordered_dict
