# dcm_qt_tree.py
"""View DICOM files in a tree using Qt and PySide"""
# Copyright (c) 2013 Padraig Looney
# This file is released under the
# pydicom (https://github.com/pydicom/pydicom)
# license, see the file LICENSE available at
# (https://github.com/pydicom/pydicom)

import pydicom
import sys
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QTreeView
import collections


class DicomTree(object):
    def __init__(self, filename):
        self.filename = filename

    def show_tree(self):
        ds = self.dicom_to_dataset(self.filename)
        dic = self.dataset_to_dic(ds)
        model = self.dic_to_model(dic)
        self.display(model)

    def array_to_model(self, array):
        model = QtGui.QStandardItemModel()
        parentItem = model.invisibleRootItem()
        for ntuple in array:
            tag = ntuple[0]
            value = ntuple[1]
            if isinstance(value, dict):
                self.recurse_dic_to_item(value, parentItem)
            else:
                item = QtGui.QStandardItem(tag + str(value))
                parentItem.appendRow(item)
        return parentItem

    def dic_to_model(self, dic):
        model = QtGui.QStandardItemModel()
        parentItem = model.invisibleRootItem()
        self.recurse_dic_to_item(dic, parentItem)
        return model

    def dataset_to_array(self, dataset):
        array = []
        for data_element in dataset:
            array.append(self.data_element_to_dic(data_element))
        return array

    def recurse_dic_to_item(self, dic, parent):
        for k in dic:
            v = dic[k]
            if isinstance(v, dict):
                item = QtGui.QStandardItem(k + ':' + str(v))
                parent.appendRow(self.recurse_dic_to_item(v, item))
            else:
                item = QtGui.QStandardItem(k + ': ' + str(v))
                parent.appendRow(item)
        return parent

    def dicom_to_dataset(self, filename):
        return pydicom.dcmread(filename, force=True)

    def data_element_to_dic(self, data_element):
        dic = collections.OrderedDict()
        if data_element.VR == "SQ":
            items = collections.OrderedDict()
            dic[data_element.name] = items
            i = 0
            for dataset_item in data_element:
                items['item ' + str(i)] = self.dataset_to_dic(dataset_item)
                i += 1
        elif data_element.name != 'Pixel Data':
            dic[data_element.name] = data_element.value
        return dic

    def dataset_to_dic(self, dataset):
        dic = collections.OrderedDict()
        for data_element in dataset:
            dic.update(self.data_element_to_dic(data_element))
        return dic

    def display(self, model):
        app = QApplication.instance()

        # create QApplication if it doesnt exist
        if not app:
            app = QApplication(sys.argv)
        tree = QTreeView()
        tree.setModel(model)
        tree.show()
        app.exec_()
        return tree


def main():
    filename = '../dicom_sample/ct.0.dcm'
    dicomTree = DicomTree(filename)
    dicomTree.show_tree()


if __name__ == "__main__":
    main()