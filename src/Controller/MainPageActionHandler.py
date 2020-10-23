import sys

from PyQt5 import QtWidgets, QtGui

from src.Model.CalculateImages import get_pixmaps
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainwindowrestructure.NewMainPage import UINewMainWindow


class MainPageActionHandler:

    def __init__(self, main_page: UINewMainWindow):
        self.main_page = main_page
        self.patient_dict_container = PatientDictContainer()

        ##############################
        # Init all actions and icons #
        ##############################

        # Open patient
        icon_open = QtGui.QIcon()
        icon_open.addPixmap(QtGui.QPixmap(":/images/Icon/open_patient.png"),
                            QtGui.QIcon.Normal,
                            QtGui.QIcon.On)
        self.action_open = QtWidgets.QAction()
        self.action_open.setIcon(icon_open)
        self.action_open.setText("Open new patient")
        self.action_open.setIconVisibleInMenu(True)

        # Save as Anonymous Action
        icon_save_as_anonymous = QtGui.QIcon()
        icon_save_as_anonymous.addPixmap(
            QtGui.QPixmap(":/images/Icon/anonlock.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_save_as_anonymous = QtWidgets.QAction()
        self.action_save_as_anonymous.setIcon(icon_save_as_anonymous)
        self.action_save_as_anonymous.setText("Save as Anonymous")
        self.action_save_as_anonymous.triggered.connect(self.anonymization_handler)

        # Exit action
        self.action_exit = QtWidgets.QAction()
        self.action_exit.setText("Exit")
        self.action_exit.triggered.connect(self.action_exit_handler)

        # Zoom In Action
        icon_zoom_in = QtGui.QIcon()
        icon_zoom_in.addPixmap(
            QtGui.QPixmap(":/images/Icon/plus.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_in = QtWidgets.QAction()
        self.action_zoom_in.setIcon(icon_zoom_in)
        self.action_zoom_in.setIconVisibleInMenu(True)
        self.action_zoom_in.setText("Zoom In")
        self.action_zoom_in.triggered.connect(self.main_page.dicom_view.zoom_in)

        # Zoom Out Action
        icon_zoom_out = QtGui.QIcon()
        icon_zoom_out.addPixmap(
            QtGui.QPixmap(":/images/Icon/minus.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_out = QtWidgets.QAction()
        self.action_zoom_out.setIcon(icon_zoom_out)
        self.action_zoom_out.setIconVisibleInMenu(True)
        self.action_zoom_out.setText("Zoom Out")
        self.action_zoom_out.triggered.connect(self.main_page.dicom_view.zoom_out)

        # Windowing Action
        icon_windowing = QtGui.QIcon()
        icon_windowing.addPixmap(
            QtGui.QPixmap(":/images/Icon/windowing.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_windowing = QtWidgets.QAction()
        self.action_windowing.setIcon(icon_windowing)
        self.action_windowing.setIconVisibleInMenu(True)
        self.action_windowing.setText("Windowing")

        # Transect Action
        icon_transect = QtGui.QIcon()
        icon_transect.addPixmap(
            QtGui.QPixmap(":/images/Icon/transect.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_transect = QtWidgets.QAction()
        self.action_transect.setIcon(icon_transect)
        self.action_transect.setIconVisibleInMenu(True)
        self.action_transect.setText("Transect")
        self.action_transect.triggered.connect(self.transect_handler)

        # Add-On Options Action
        icon_add_ons = QtGui.QIcon()
        icon_add_ons.addPixmap(
            QtGui.QPixmap(":/images/Icon/management.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_add_ons = QtWidgets.QAction()
        self.action_add_ons.setIcon(icon_add_ons)
        self.action_add_ons.setIconVisibleInMenu(True)
        self.action_add_ons.setText("Add-On Options")
        self.action_add_ons.triggered.connect(self.add_on_options_handler)

        # Export Clinical Data Action
        self.action_clinical_data_export = QtWidgets.QAction()
        self.action_clinical_data_export.setText("Export Clinical Data")
        # TODO self.action_clinical_data_export.triggered.connect(clinical data check)

        # Export Pyradiomics Action
        self.action_pyradiomics_export = QtWidgets.QAction()
        self.action_pyradiomics_export.setText("Export Pyradiomics")

    def windowing_handler(self, state, text):
        """
        Function triggered when a window is selected from the menu.
        :param state: Variable not used. Present to be able to use a lambda function.
        :param text: The name of the window selected.
        """
        # Get the values for window and level from the dict
        windowing_limits = self.patient_dict_container.get("dict_windowing")[text]

        # Set window and level to the new values
        window = windowing_limits[0]
        level = windowing_limits[1]

        # Update the dictionary of pixmaps with the update window and level values
        pixmaps = self.patient_dict_container.get("pixmaps")
        pixel_values = self.patient_dict_container.get("pixel_values")
        new_pixmaps = get_pixmaps(pixel_values, window, level)

        self.patient_dict_container.set("window", window)
        self.patient_dict_container.set("level", level)
        self.patient_dict_container.set("pixmaps", new_pixmaps)

        self.main_page.update_views()

    def anonymization_handler(self):
        """
        Function triggered when the Anonymization button is pressed from the menu.
        """

        save_reply = QtWidgets.QMessageBox.information(
            self.main_page.main_window_instance,
            "Confirmation",
            "Are you sure you want to perform anonymization?",
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )

        if save_reply == QtWidgets.QMessageBox.Yes:
            raw_dvh = self.patient_dict_container.get("raw_dvh")
            hashed_path = self.main_page.call_class.runAnonymization(raw_dvh)
            self.patient_dict_container.set("hashed_path", hashed_path)
            # now that the radiomics data can just get copied across... maybe skip this?
            radiomics_reply = QtWidgets.QMessageBox.information(
                self.main_page.main_window_instance,
                "Confirmation",
                "Are you sure you want to perform radiomics?",
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No
            )
            if radiomics_reply == QtWidgets.QMessageBox.Yes:
                self.main_page.pyradi_trigger.emit(
                    self.patient_dict_container.path,
                    self.patient_dict_container.filepaths,
                    hashed_path
                )

    def transect_handler(self):
        """
        Function triggered when the Transect button is pressed from the menu.
        """
        id = self.main_page.dicom_view.slider.value()
        dt = self.patient_dict_container.dataset[id]
        rowS = dt.PixelSpacing[0]
        colS = dt.PixelSpacing[1]
        dt.convert_pixel_data()
        pixmap = self.patient_dict_container.get("pixmaps")[id]
        self.main_page.call_class.runTransect(
            self.main_page,
            self.main_page.dicom_view.view,
            pixmap,
            dt._pixel_array.transpose(),
            rowS,
            colS
        )

    def add_on_options_handler(self):
        self.main_page.add_on_options_controller.show_add_on_options()

    def action_exit_handler(self):
        sys.exit()
