import sys
import pydicom
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QTreeView
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
        dataset = pydicom.dcmread(filename)
        return dataset

    def show_tree(self):
        ds = self.read_dcm(self.filename)
        dict = self.dataset_to_dict(ds)
        model = self.dict_to_model(dict)
        self.display(model)

    def recurse_dict_to_item(self, dict, parent):
        # For every key in the dictionary
        for key in dict:
            # The value of current key
            value = dict[key]
            # If the value is a dictionary
            if isinstance(value, type(dict)):
                # Recurse until leaf
                item = QtGui.QStandardItem(key)
                parent.appendRow(self.recurse_dict_to_item(value, item))
            else:
                # If the value is a simple item
                # Append it.
                item = QtGui.QStandardItem(key + ': ' + str(value[0]) + " "+ str(value[1]) + " " + str(value[2]) \
                                           + " " + str(value[3]))
                parent.appendRow(item)
        return parent

    def dict_to_model(self, dict):
        # Create a QstandardItemModel for the tree data
        model = QtGui.QStandardItemModel()
        # Set the parent item with a ghost root
        parentItem = model.invisibleRootItem()
        # Recursively get the tree
        self.recurse_dict_to_item(dict, parentItem)
        return model

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
                # in the dictonary
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

    # Display the TreeView
    def display(self, model):
        app = QApplication.instance()

        if not app:
            app = QApplication(sys.argv)

        # Create an instance of QTreeView
        tree = QTreeView()
        # Set the model to the tree
        tree.setModel(model)
        # Show the tree
        tree.show()

        app.exec_()

        return tree




# def main():
#     filename = 'dicom_sample/ct.0.dcm'
#     dicomTree = DicomTree(filename)
#     dicomTree.show_tree()
#
# if __name__ == '__main__':
#     path = 'dicom_sample/ct.0.dcm'
#     ds = pydicom.dcmread(path)
#     # ls = get_tree(ds, 0)
#     # for i in ls:
#     #     print(i)
#     #
#     # print(ds)
#
#     main()
#     dict = get_basic_info(ds)
#     print(dict)