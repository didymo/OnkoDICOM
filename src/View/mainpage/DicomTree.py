from PyQt5 import QtWidgets, QtCore, QtGui
from src.Model.GetPatientInfo import *


class DicomTreeUI(object):
	"""
	Manage all functionalities related to the DICOM Tree tab.
	"""

	def __init__(self, mainWindow):
		"""
		Initialize the information useful for creating the DICOM Tree.
		Add the DICOM Tree tab to the window of the main page.

		:param mainWindow:
		 the window of the main page
		"""
		self.window = mainWindow
		self.pixmaps = mainWindow.pixmaps
		self.selector = self.selector_combobox()
		mainWindow.tab2_DICOM_tree = QtWidgets.QWidget()
		mainWindow.tab2_DICOM_tree.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_tree()
		self.init_layout()


	def init_layout(self):
		"""
		Initialize the layout for the DICOM Tree tab.
		Add the combobox and the DICOM tree in the layout.
		Add the whole container 'tab2_DICOM_tree' as a tab in the main page.

		:param mainWindow:
		 the window of the main page
		"""
		self.layout = QtWidgets.QVBoxLayout(self.window.tab2_DICOM_tree)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(self.selector, QtCore.Qt.AlignLeft)
		self.layout.addWidget(self.treeView)
		self.window.tab2.addTab(self.window.tab2_DICOM_tree, "DICOM Tree")


	def init_tree(self):
		"""
		:return: An initial tree.
		"""
		self.treeView = QtWidgets.QTreeView(self.window.tab2_DICOM_tree)
		self.treeView.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_headers_tree()
		self.init_parameters_tree()


	def init_headers_tree(self):
		"""
		Initialize the model and the headers of the DICOM tree
		"""
		self.modelTree = QtGui.QStandardItemModel(0, 5)
		self.modelTree.setHeaderData(0, QtCore.Qt.Horizontal, "Name")
		self.modelTree.setHeaderData(1, QtCore.Qt.Horizontal, "Value")
		self.modelTree.setHeaderData(2, QtCore.Qt.Horizontal, "Tag")
		self.modelTree.setHeaderData(3, QtCore.Qt.Horizontal, "VM")
		self.modelTree.setHeaderData(4, QtCore.Qt.Horizontal, "VR")
		self.treeView.setModel(self.modelTree)


	def init_parameters_tree(self):
		"""
		Set the parameters of the tree view.
		"""
		self.treeView.header().resizeSection(0, 250)
		self.treeView.header().resizeSection(1, 350)
		self.treeView.header().resizeSection(2, 100)
		self.treeView.header().resizeSection(3, 50)
		self.treeView.header().resizeSection(4, 50)
		self.treeView.header().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
		self.treeView.setEditTriggers(
			QtWidgets.QAbstractItemView.NoEditTriggers)
		self.treeView.setAlternatingRowColors(True)
		self.treeView.expandAll()


	def selector_combobox(self):
		"""
		:return: Combobox to select the tree of a dataset.
		"""
		combobox = QtWidgets.QComboBox()
		combobox.setFocusPolicy(QtCore.Qt.NoFocus)
		combobox.setStyleSheet("QComboBox {font: 75 \"Laksaman\";"
							   "combobox-popup: 0;"
							   "background-color: #efefef; }"
							   )
		combobox.addItem("Select a DICOM dataset...")
		combobox.addItem("RT Dose")
		combobox.addItem("RTSS")
		for i in range(len(self.pixmaps) - 1):
			combobox.addItem("CT Image Slice " + str(i + 1))
		combobox.activated.connect(self.item_selected)
		combobox.setFixedSize(QtCore.QSize(200, 31))

		return combobox


	def item_selected(self, index):
		"""
		Function triggered when an item of the combobox is selected.
		Update the DICOM Tree view.

		:param index:
		 index of the item selected.
		"""
		# CT Scans
		if index > 2:
			self.updateTree(True, index - 3, "")
		# RT Dose
		elif index == 1:
			self.updateTree(False, 0, "RT Dose")
		# RTSS
		elif index == 2:
			self.updateTree(False, 0, "RTSS")


	def updateTree(self, ct_file, id, name):
		"""
		Update the DICOM Tree view.

		:param ct_file:
		 Boolean indicating if it is a CT file or not.
		:param id:
		 Id of the selected CT file
		:param name:
		 Name of the selected dataset if it is not a CT file ("RT Dose" or "RTSS")
		"""
		self.init_headers_tree()

		if ct_file:
			filename = self.window.filepaths[id]
			dicomTreeSlice = DicomTree(filename)
			dict_tree = dicomTreeSlice.dict

		elif name == "RT Dose":
			dict_tree = self.window.dictDicomTree_rtdose

		elif name == "RTSS":
			dict_tree = self.window.dictDicomTree_rtss

		else:
			dict_tree = None
			print("Error filename in updateTree function")

		# Set the parent item with a ghost root
		parentItem = self.modelTree.invisibleRootItem()
		# Recursively get the tree
		self.recurseBuildModel(dict_tree, parentItem)
		self.treeView.setModel(self.modelTree)
		self.layout.addWidget(self.treeView)


	def recurseBuildModel(self, dict_tree, parent):
		"""
		Update recursively the model used for the DICOM Tree View

		:param dict:
		 The dictionary to be displayed.
		:param parent:
		 parent node of the tree
		"""
		for key in dict_tree:
			value = dict_tree[key]
			# If the value is a dictionary
			if isinstance(value, type(dict_tree)):
				# Recurse until leaf
				itemChild = QtGui.QStandardItem(key)
				parent.appendRow(self.recurseBuildModel(value, itemChild))
			else:
				# If the value is a simple item
				# Append it.
				item = [QtGui.QStandardItem(key),
						QtGui.QStandardItem(str(value[0])),
						QtGui.QStandardItem(str(value[1])),
						QtGui.QStandardItem(str(value[2])),
						QtGui.QStandardItem(str(value[3]))]
				parent.appendRow(item)
		return parent
