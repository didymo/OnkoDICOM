from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.CalculateImages import *
from copy import deepcopy

class MenuBar(object):
	"""
	Manage all actions related to the menu bar and the tool bar.
	- Build menu bar and tool bar.
	- Assign actions to items of these two bars.
	"""

	def __init__(self, main_window):
		"""
		Build and add menu bar and tool bar to the window of the main page.

		:param main_window:
		 the window of the main page
		"""
		self.window = main_window
		self.handlers = MenuHandler(main_window)
		self.init_icons()
		self.create_actions()
		self.create_menubar()
		self.create_toolbar()
		self.retranslate()

	def init_icons(self):
		"""
		Initialize all icons used for menu bar and toolbar
		"""
		self.iconOpen = QtGui.QIcon()
		self.iconOpen.addPixmap(QtGui.QPixmap(":/images/Icon/open_patient.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconAnonymize_and_Save = QtGui.QIcon()
		self.iconAnonymize_and_Save.addPixmap(QtGui.QPixmap(":/images/Icon/anonlock.png"), QtGui.QIcon.Normal,
											  QtGui.QIcon.On)
		self.iconZoom_In = QtGui.QIcon()
		self.iconZoom_In.addPixmap(QtGui.QPixmap(":/images/Icon/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconZoom_Out = QtGui.QIcon()
		self.iconZoom_Out.addPixmap(QtGui.QPixmap(":/images/Icon/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconWindowing = QtGui.QIcon()
		self.iconWindowing.addPixmap(QtGui.QPixmap(":/images/Icon/windowing.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconTransect = QtGui.QIcon()
		self.iconTransect.addPixmap(QtGui.QPixmap(":/images/Icon/transect.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		# # Icons for creating ROIs
		# self.iconBrush = QtGui.QIcon()
		# self.iconBrush.addPixmap(QtGui.QPixmap(":/images/Icon/ROI_Brush.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		# self.iconIsodose = QtGui.QIcon()
		# self.iconIsodose.addPixmap(QtGui.QPixmap(":/images/Icon/ROI_Isodose.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconAddOn = QtGui.QIcon()
		self.iconAddOn.addPixmap(QtGui.QPixmap(":/images/Icon/management.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.iconExport = QtGui.QIcon()
		self.iconExport.addPixmap(QtGui.QPixmap(":/images/Icon/export.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)

	def create_actions(self):
		"""
		Create actions used for menu and tool bars.
		"""
		# Open Patient Action
		self.actionOpen = QtWidgets.QAction(self.window)
		self.actionOpen.setIcon(self.iconOpen)
		self.actionOpen.setIconVisibleInMenu(True)

		# # Import Action
		# self.actionImport = QtWidgets.QAction(self.window)

		# # Save Action
		# self.actionSave = QtWidgets.QAction(self.window)

		# Save as Anonymous Action
		self.actionSave_as_Anonymous = QtWidgets.QAction(self.window)
		self.actionSave_as_Anonymous.triggered.connect(self.handlers.anonymization_handler)

		# Exit Action
		self.actionExit = QtWidgets.QAction(self.window)

		# # All the Edit actions
		# # Undo Action
		# self.actionUndo = QtWidgets.QAction(self.window)
		# # Redo Action
		# self.actionRedo = QtWidgets.QAction(self.window)
		# # Rename ROI Action
		# self.actionRename_ROI = QtWidgets.QAction(self.window)
		# # Delete ROI Action
		# self.actionDelete_ROI = QtWidgets.QAction(self.window)

		# Zoom In Action
		self.actionZoom_In = QtWidgets.QAction(self.window)
		self.actionZoom_In.setIcon(self.iconZoom_In)
		self.actionZoom_In.setIconVisibleInMenu(True)
		self.actionZoom_In.triggered.connect(self.window.dicom_view.zoomIn)

		# Zoom Out Action
		self.actionZoom_Out = QtWidgets.QAction(self.window)
		self.actionZoom_Out.setIcon(self.iconZoom_Out)
		self.actionZoom_Out.setIconVisibleInMenu(True)
		self.actionZoom_Out.triggered.connect(self.window.dicom_view.zoomOut)

		# Windowing Action
		self.actionWindowing = QtWidgets.QAction(self.window)
		self.actionWindowing.setIcon(self.iconWindowing)
		self.actionWindowing.setIconVisibleInMenu(True)
		# self.init_windowing_menu()

		# Transect Action
		self.actionTransect = QtWidgets.QAction(self.window)
		self.actionTransect.setIcon(self.iconTransect)
		self.actionTransect.setIconVisibleInMenu(True)
		self.actionTransect.triggered.connect(self.handlers.transect_handler)

		# # ROI by brush Action
		# self.actionBrush = QtWidgets.QAction(self.window)
		# self.actionBrush.setIcon(self.iconBrush)
		# self.actionBrush.setIconVisibleInMenu(True)

		# # ROI by Isodose Action
		# self.actionIsodose = QtWidgets.QAction(self.window)
		# self.actionIsodose.setIcon(self.iconIsodose)
		# self.actionIsodose.setIconVisibleInMenu(True)

		# Add-On Options Action
		self.actionAddOn = QtWidgets.QAction(self.window)
		self.actionAddOn.setIcon(self.iconAddOn)
		self.actionAddOn.setIconVisibleInMenu(True)
		self.actionAddOn.triggered.connect(self.handlers.add_on_options_handler)

		# Anonymize and Save Action
		self.actionAnonymize_and_Save = QtWidgets.QAction(self.window)
		self.actionAnonymize_and_Save.setIcon(self.iconAnonymize_and_Save)
		self.actionAnonymize_and_Save.setIconVisibleInMenu(True)
		self.actionAnonymize_and_Save.triggered.connect(self.handlers.anonymization_handler)

		# Export DVH Spreadsheet Action
		if self.window.has_rtss and self.window.has_rtdose:
			self.actionDVH_Spreadsheet = QtWidgets.QAction(self.window)
			self.actionDVH_Spreadsheet.triggered.connect(self.window.dvh.export_csv)

		# Export Clinical Data Action
		self.actionClinical_Data = QtWidgets.QAction(self.window)
		self.actionClinical_Data.triggered.connect(self.window.clinicalDataCheck)

		# Export Pyradiomics Action
		self.actionPyradiomics = QtWidgets.QAction(self.window)


	def init_windowing_menu(self):
		"""
		Create the menu for Windowing with the list of all the windows.
		"""
		_translate = QtCore.QCoreApplication.translate

		# Get the right order for windowing names
		names_ordered = sorted(self.window.dict_windowing.keys())
		if 'Normal' in self.window.dict_windowing.keys():
			old_index = names_ordered.index('Normal')
			names_ordered.insert(0, names_ordered.pop(old_index))

		# Create actions for each windowing items
		for name in names_ordered:
			text = str(name)
			actionWindowingItem = QtWidgets.QAction(self.window)
			actionWindowingItem.triggered.connect(
				lambda state, text=name: self.handlers.windowing_handler(state, text))
			self.menuWindowing.addAction(actionWindowingItem)
			actionWindowingItem.setText(_translate("MainWindow", text))


	def create_menubar(self):
		"""
		Build the menu bar.
		"""
		# Menu Bar
		self.menubar = QtWidgets.QMenuBar(self.window)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 901, 35))
		self.window.setMenuBar(self.menubar)
		self.menubar.setFocusPolicy(QtCore.Qt.NoFocus)

		# Menu Bar: File, Edit, Tools, Help
		self.menuFile = QtWidgets.QMenu(self.menubar)
		# self.menuEdit = QtWidgets.QMenu(self.menubar)
		self.menuTools = QtWidgets.QMenu(self.menubar)
		self.menuHelp = QtWidgets.QMenu(self.menubar)

		# Create sub-menu for Windowing item
		self.menuWindowing = QtWidgets.QMenu(self.menuTools)
		self.menuWindowing.setIcon(self.iconWindowing)
		self.init_windowing_menu()

		# # Create sub-menu for ROI Creation item
		# self.menuROI_Creation = QtWidgets.QMenu(self.menuTools)
		# self.menuROI_Creation.addAction(self.actionBrush)
		# self.menuROI_Creation.addAction(self.actionIsodose)

		# Create sub-menu for Export item
		self.menuExport = QtWidgets.QMenu(self.menuTools)
		self.menuExport.setIcon(self.iconExport)
		if self.window.has_rtss and self.window.has_rtdose:
			self.menuExport.addAction(self.actionDVH_Spreadsheet)
		self.menuExport.addAction(self.actionClinical_Data)
		self.menuExport.addAction(self.actionPyradiomics)

		# Menu "File"
		self.menuFile.addAction(self.actionOpen)
		# self.menuFile.addAction(self.actionImport)
		self.menuFile.addSeparator()
		# self.menuFile.addAction(self.actionSave)
		self.menuFile.addAction(self.actionSave_as_Anonymous)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionExit)

		# # Menu "Edit"
		# self.menuEdit.addAction(self.actionUndo)
		# self.menuEdit.addAction(self.actionRedo)
		# self.menuEdit.addSeparator()
		# self.menuEdit.addAction(self.actionRename_ROI)
		# self.menuEdit.addAction(self.actionDelete_ROI)

		# Menu "Tools"
		self.menuTools.addAction(self.actionZoom_In)
		self.menuTools.addAction(self.actionZoom_Out)
		self.menuTools.addAction(self.menuWindowing.menuAction())
		self.menuTools.addAction(self.actionTransect)
		# self.menuTools.addAction(self.menuROI_Creation.menuAction())
		self.menuTools.addAction(self.actionAddOn)
		self.menuTools.addSeparator()
		self.menuTools.addAction(self.menuExport.menuAction())
		self.menuTools.addAction(self.actionAnonymize_and_Save)
		self.menuTools.setFocusPolicy(QtCore.Qt.NoFocus)

		# Add the four menus to the menu bar
		self.menubar.addAction(self.menuFile.menuAction())
		# self.menubar.addAction(self.menuEdit.menuAction())
		self.menubar.addAction(self.menuTools.menuAction())
		self.menubar.addAction(self.menuHelp.menuAction())


	def create_toolbar(self):
		"""
		Build the tool bar.
		"""
		# Drop-down list for Windowing button on toolbar
		self.windowingButton = QtWidgets.QToolButton()
		self.windowingButton.setMenu(self.menuWindowing)
		self.windowingButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		self.windowingButton.setIcon(self.iconWindowing)
		self.windowingButton.setFocusPolicy(QtCore.Qt.NoFocus)

		# Drop-down list for Export button on toolbar
		self.exportButton = QtWidgets.QToolButton()
		self.exportButton.setMenu(self.menuExport)
		self.exportButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
		self.exportButton.setIcon(self.iconExport)
		self.exportButton.setFocusPolicy(QtCore.Qt.NoFocus)

		# Set Tool Bar
		self.toolBar = QtWidgets.QToolBar(self.window)
		self.toolBar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.toolBar.setMovable(False)
		self.window.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

		# Spacer for the toolbar
		spacer = QtWidgets.QWidget()
		spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		spacer.setFocusPolicy(QtCore.Qt.NoFocus)

		self.toolBar.addAction(self.actionOpen)
		self.toolBar.addSeparator()
		self.toolBar.addAction(self.actionZoom_In)
		self.toolBar.addAction(self.actionZoom_Out)
		self.toolBar.addSeparator()
		self.toolBar.addWidget(self.windowingButton)
		self.toolBar.addSeparator()
		self.toolBar.addAction(self.actionTransect)
		self.toolBar.addSeparator()
		# self.toolBar.addAction(self.actionBrush)
		# self.toolBar.addAction(self.actionIsodose)
		# self.toolBar.addSeparator()
		self.toolBar.addAction(self.actionAddOn)
		self.toolBar.addWidget(spacer)
		self.toolBar.addWidget(self.exportButton)
		self.toolBar.addAction(self.actionAnonymize_and_Save)


	def retranslate(self):
		"""
		Give names for all items in the menu bar and tool bar.
		"""
		_translate = QtCore.QCoreApplication.translate

		# Menu labels
		self.menuFile.setTitle(_translate("MainWindow", "File"))
		# self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
		self.menuTools.setTitle(_translate("MainWindow", "Tools"))
		self.menuWindowing.setTitle(_translate("MainWindow", "Windowing"))
		# self.menuROI_Creation.setTitle(_translate("MainWindow", "ROI Creation"))
		self.menuExport.setTitle(_translate("MainWindow", "Export"))
		self.menuHelp.setTitle(_translate("MainWindow", "Help"))
		self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))

		# Action labels
		self.actionOpen.setText(_translate("MainWindow", "Open Patient..."))
		# self.actionImport.setText(_translate("MainWindow", "Import..."))
		# self.actionSave.setText(_translate("MainWindow", "Save"))
		self.actionSave_as_Anonymous.setText(_translate("MainWindow", "Save as Anonymous..."))
		self.actionExit.setText(_translate("MainWindow", "Exit"))
		# self.actionUndo.setText(_translate("MainWindow", "Undo"))
		# self.actionRedo.setText(_translate("MainWindow", "Redo"))
		# self.actionRename_ROI.setText(_translate("MainWindow", "Rename ROI..."))
		# self.actionDelete_ROI.setText(_translate("MainWindow", "Delete ROI..."))
		self.actionZoom_In.setText(_translate("MainWindow", "Zoom In"))
		self.actionZoom_Out.setText(_translate("MainWindow", "Zoom Out"))
		self.actionWindowing.setText(_translate("MainWindow", "Windowing"))
		self.actionTransect.setText(_translate("MainWindow", "Transect"))
		# self.actionBrush.setText(_translate("MainWindow", "ROI by Brush"))
		# self.actionIsodose.setText(_translate("MainWindow", "ROI by Isodose"))
		self.actionAddOn.setText(_translate("MainWindow", "Add-On Options..."))
		self.actionAnonymize_and_Save.setText(_translate("MainWindow", "Anonymize and Save"))
		if self.window.has_rtss and self.window.has_rtdose:
			self.actionDVH_Spreadsheet.setText(_translate("MainWindow", "DVH"))
		self.actionClinical_Data.setText(_translate("MainWindow", "Clinical Data"))
		self.actionPyradiomics.setText(_translate("MainWindow", "Pyradiomics"))
	
	
class MenuHandler(object):
	"""
	Gather functions to be triggered and used in the menu and tool bars.
	Note: The triggered functions related to one of the four tabs (DICOM View, DVH, DICOM Tree and Clinical	Data)
	are managed by their corresponding classes.
	"""

	def __init__(self, main_window):
		"""
		Initialization of the handler class.
		:param main_window:
		 the window of the main page
		"""
		self.main_window = main_window
		
	
	def windowing_handler(self, state, text):
		"""
		Function triggered when a window is selected from the menu.
		:param state: Variable not used. Present to be able to use a lambda function.
		:param text: The name of the window selected.
		"""
		# Get the values for window and level from the dict
		windowing_limits = self.main_window.dict_windowing[text]

		# Set window and level to the new values
		self.main_window.window = windowing_limits[0]
		self.main_window.level = windowing_limits[1]

		# Update the dictionary of pixmaps with the updated window and level values
		self.main_window.pixmaps = get_pixmaps(self.main_window.pixel_values,
											   self.main_window.window, self.main_window.level)
		self.main_window.dicom_view.update_view()


	def anonymization_handler(self):
		"""
		Function triggered when the Anonymization button is pressed from the menu.
		"""
		SaveReply = QtWidgets.QMessageBox.information(self.main_window, "Confirmation",
													  "Are you sure you want to perform anonymization?",
													  QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
		if SaveReply == QtWidgets.QMessageBox.Yes:
			self.main_window.hashed_path = self.main_window.callClass.runAnonymization(self.main_window)
			self.main_window.pyradi_trigger.emit(self.main_window.path, self.main_window.filepaths,
												 self.main_window.hashed_path)
		if SaveReply == QtWidgets.QMessageBox.No:
			pass
	
	
	def transect_handler(self):
		"""
		Function triggered when the Transect button is pressed from the menu.
		"""
		id = self.main_window.dicom_view.slider.value()
		dt = self.main_window.dataset[id]
		rowS = dt.PixelSpacing[0]
		colS = dt.PixelSpacing[1]
		dt.convert_pixel_data()
		self.main_window.callClass.runTransect(self.main_window, self.main_window.dicom_view.view,
											   self.main_window.pixmaps[id], dt._pixel_array.transpose(), rowS, colS)
	
	
	def add_on_options_handler(self):
		"""
		Function triggered when the Add-On Options button is pressed from the menu.
		"""
		self.main_window.callManager.show_add_on_options()