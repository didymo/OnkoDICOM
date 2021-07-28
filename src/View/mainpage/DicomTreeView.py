from PySide6 import QtWidgets, QtGui, QtCore

from src.Model.GetPatientInfo import DicomTree
from src.Model.PatientDictContainer import PatientDictContainer


class DicomTreeView(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.pixmaps = self.patient_dict_container.get("pixmaps")

        self.dicom_tree_layout = QtWidgets.QVBoxLayout()
        self.dicom_tree_layout.setContentsMargins(0, 0, 0, 0)

        self.selector = self.create_selector_combobox()

        self.tree_view = QtWidgets.QTreeView()
        self.model_tree = QtGui.QStandardItemModel(0, 5)
        self.init_headers_tree()
        self.tree_view.setModel(self.model_tree)
        self.init_parameters_tree()

        self.dicom_tree_layout.addWidget(
            self.selector,
            QtCore.Qt.AlignLeft
            | QtCore.Qt.AlignLeft)
        self.dicom_tree_layout.addWidget(self.tree_view)
        self.setLayout(self.dicom_tree_layout)

    def init_headers_tree(self):
        self.model_tree.setHeaderData(0, QtCore.Qt.Horizontal, "Name")
        self.model_tree.setHeaderData(1, QtCore.Qt.Horizontal, "Value")
        self.model_tree.setHeaderData(2, QtCore.Qt.Horizontal, "Tag")
        self.model_tree.setHeaderData(3, QtCore.Qt.Horizontal, "VM")
        self.model_tree.setHeaderData(4, QtCore.Qt.Horizontal, "VR")

    def init_parameters_tree(self):
        self.tree_view.header().resizeSection(0, 250)
        self.tree_view.header().resizeSection(1, 350)
        self.tree_view.header().resizeSection(2, 100)
        self.tree_view.header().resizeSection(3, 50)
        self.tree_view.header().resizeSection(4, 50)
        self.tree_view.header().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.tree_view.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
            | QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.expandAll()

    def create_selector_combobox(self):
        combobox = QtWidgets.QComboBox()
        combobox.setFocusPolicy(QtCore.Qt.NoFocus)
        combobox.addItem("Select a DICOM dataset...")

        # determines which files are included
        self.special_files = []

        if self.patient_dict_container.has_modality("rtss"):
            combobox.addItem("RT Structure Set")
            self.special_files.append("rtss")

        if self.patient_dict_container.has_modality("rtdose"):
            combobox.addItem("RT Dose")
            self.special_files.append("rtdose")

        if self.patient_dict_container.has_modality("rtplan"):
            combobox.addItem("RT Plan")
            self.special_files.append("rtplan")

        for i in range(len(self.pixmaps)):
            combobox.addItem("Image Slice " + str(i + 1))

        combobox.activated.connect(self.item_selected)
        combobox.setFixedSize(QtCore.QSize(200, 31))
        combobox.setObjectName("DicomTreeviewComboBox")
        return combobox

    def item_selected(self, index):
        if index <= len(self.special_files) and index != 0:
            self.update_tree(False, 0, self.special_files[index-1])
        elif index > len(self.special_files):
            self.update_tree(True, index - len(self.special_files) - 1, "")

    def update_tree(self, image_slice, id, name):
        """
        Update the DICOM Tree view.
        :param image_slice: Boolean indicating if it is an image slice or not
        :param id: ID for the selected file
        :param name: Name of the selected dataset if not an image file
        :return:
        """
        self.model_tree.clear()

        if image_slice:
            filename = self.patient_dict_container.filepaths[id]
            dicom_tree_slice = DicomTree(filename)
            dict_tree = dicom_tree_slice.dict

        elif name == "rtdose":
            dict_tree = self.patient_dict_container.get(
                "dict_dicom_tree_rtdose")

        elif name == "rtss":
            dict_tree = self.patient_dict_container.get(
                "dict_dicom_tree_rtss")

        elif name == "rtplan":
            dict_tree = self.patient_dict_container.get(
                "dict_dicom_tree_rtplan")

        else:
            dict_tree = None
            print("Error filename in update_tree function")

        parent_item = self.model_tree.invisibleRootItem()
        self.recurse_build_model(dict_tree, parent_item)
        self.init_headers_tree()
        self.tree_view.setModel(self.model_tree)
        self.init_parameters_tree()
        self.dicom_tree_layout.addWidget(self.tree_view)

    def recurse_build_model(self, dict_tree, parent):
        """
        Update recursively the model used for the DICOM Tree view
        :param dict_tree: The dictionary to be displayed
        :param parent: Parent node of the tree
        :return:
        """
        for key in dict_tree:
            value = dict_tree[key]
            # If the value is a dictionary
            if isinstance(value, type(dict_tree)):
                # Recurse until leaf
                item_child = QtGui.QStandardItem(key)
                parent.appendRow(self.recurse_build_model(value, item_child))
            else:
                # If the value is a simple item, append it
                item = [QtGui.QStandardItem(key),
                        QtGui.QStandardItem(str(value[0])),
                        QtGui.QStandardItem(str(value[1])),
                        QtGui.QStandardItem(str(value[2])),
                        QtGui.QStandardItem(str(value[3]))]
                parent.appendRow(item)
        return parent
