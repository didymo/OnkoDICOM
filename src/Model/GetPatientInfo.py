import pydicom
import collections


def get_tree(ds, label=0):
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


# Get patient name, ID, gender and DOB
def get_basic_info(ds):
    dict_basic_info = {}
    dict_basic_info['name'] = str(ds.PatientName)
    dict_basic_info['id'] = str(ds.PatientID)
    dict_basic_info['gender'] = str(ds.PatientSex)
    dict_basic_info['dob'] = str(ds.PatientBirthDate)
    return dict_basic_info


# Return a dictionary where key = index of the slice and value is the Instance UID
def dict_instanceUID(dict_ds):
    res = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss']

    for ds in dict_ds:
        if ds not in non_img_type:
            index = int(ds)
            img_ds = dict_ds[ds]
            res[index] = img_ds.SOPInstanceUID
    return res


# =========   This is a class for DICOM TREE   ===============
class DicomTree(object):
    def __init__(self, filename):
        self.filename = filename
        self.dataset = self.read_dcm(filename)
        self.dict = self.dataset_to_dict(self.dataset)

    # Read dicom file to dataset
    def read_dcm(self, filename):
        dataset = pydicom.dcmread(filename, force=True)
        return dataset

    # Convert the data_element to an ordered dicitonary
    def data_element_to_dict(self, data_element):
        # Create an oredered dictionary
        dict = collections.OrderedDict()
        # If current data element is a sequence
        if data_element.VR == 'SQ':
            # Create an ordered dictionary for the items in the sequence.
            items = collections.OrderedDict()
            # Key: element name, Value: item
            dict[data_element.name] = items
            # Temporary value for indexing
            tmp = 0
            # For every items in the sequence element
            for dataset_item in data_element:
                # Convert the item to dictionary
                # And store it as key: 'item: index num', value: dictionary of the item
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
            dict[data_element.name] = temp_list
        return dict

    # Convert the dataset to an ordered dictionary
    def dataset_to_dict(self, dataset):
        # Create an ordered dictionary
        dict = collections.OrderedDict()
        # For each element in the dataset
        for data_element in dataset:
            # Update the dictionary with the key/value pairs from dictionary.
            # The dictionary is converted from every data_element.
            dict.update(self.data_element_to_dict(data_element))
        return dict