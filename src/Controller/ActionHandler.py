import sys

from PyQt5 import QtGui, QtWidgets

from src.Model.CalculateImages import get_pixmaps
from src.Model.PatientDictContainer import PatientDictContainer


class ActionHandler:

    def __init__(self, main_page):
        self.main_page = main_page
        self.patient_dict_container = PatientDictContainer()

        ##############################
        # Init all actions and icons #
        ##############################

        # Open patient
        self.icon_open = QtGui.QIcon()
        self.icon_open.addPixmap(
            QtGui.QPixmap("src/Icon/open_patient.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On)
        self.action_open = QtWidgets.QAction()
        self.action_open.setIcon(self.icon_open)
        self.action_open.setText("Open new patient")
        self.action_open.setIconVisibleInMenu(True)

        # Save as Anonymous Action
        self.icon_save_as_anonymous = QtGui.QIcon()
        self.icon_save_as_anonymous.addPixmap(
            QtGui.QPixmap("src/Icon/anonlock.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_save_as_anonymous = QtWidgets.QAction()
        self.action_save_as_anonymous.setIcon(self.icon_save_as_anonymous)
        self.action_save_as_anonymous.setText("Save as Anonymous")
        self.action_save_as_anonymous.triggered.connect(self.anonymization_handler)

        # Exit action
        self.action_exit = QtWidgets.QAction()
        self.action_exit.setText("Exit")
        self.action_exit.triggered.connect(self.action_exit_handler)

        # Zoom In Action
        self.icon_zoom_in = QtGui.QIcon()
        self.icon_zoom_in.addPixmap(
            QtGui.QPixmap("src/Icon/plus.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_in = QtWidgets.QAction()
        self.action_zoom_in.setIcon(self.icon_zoom_in)
        self.action_zoom_in.setIconVisibleInMenu(True)
        self.action_zoom_in.setText("Zoom In")
        self.action_zoom_in.triggered.connect(self.main_page.dicom_view.zoom_in)

        # Zoom Out Action
        self.icon_zoom_out = QtGui.QIcon()
        self.icon_zoom_out.addPixmap(
            QtGui.QPixmap("src/Icon/minus.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_out = QtWidgets.QAction()
        self.action_zoom_out.setIcon(self.icon_zoom_out)
        self.action_zoom_out.setIconVisibleInMenu(True)
        self.action_zoom_out.setText("Zoom Out")
        self.action_zoom_out.triggered.connect(self.main_page.dicom_view.zoom_out)

        # Windowing Action
        self.icon_windowing = QtGui.QIcon()
        self.icon_windowing.addPixmap(
            QtGui.QPixmap("src/Icon/windowing.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_windowing = QtWidgets.QAction()
        self.action_windowing.setIcon(self.icon_windowing)
        self.action_windowing.setIconVisibleInMenu(True)
        self.action_windowing.setText("Windowing")

        # Transect Action
        self.icon_transect = QtGui.QIcon()
        self.icon_transect.addPixmap(
            QtGui.QPixmap("src/Icon/transect.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_transect = QtWidgets.QAction()
        self.action_transect.setIcon(self.icon_transect)
        self.action_transect.setIconVisibleInMenu(True)
        self.action_transect.setText("Transect")
        self.action_transect.triggered.connect(self.transect_handler)

        # Add-On Options Action
        self.icon_add_ons = QtGui.QIcon()
        self.icon_add_ons.addPixmap(
            QtGui.QPixmap("src/Icon/management.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_add_ons = QtWidgets.QAction()
        self.action_add_ons.setIcon(self.icon_add_ons)
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

        # Export DVH Action
        self.action_dvh_export = QtWidgets.QAction()
        self.action_dvh_export.setText("Export DVH")
        self.action_dvh_export.triggered.connect(self.export_dvh_handler)

        # Create Windowing menu
        self.menu_windowing = QtWidgets.QMenu()
        self.init_windowing_menu()

        # Create Export menu
        self.icon_export = QtGui.QIcon()
        self.icon_export.addPixmap(
            QtGui.QPixmap("src/Icon/export.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.menu_export = QtWidgets.QMenu()
        self.menu_export.setTitle("Export")
        self.menu_export.addAction(self.action_clinical_data_export)
        self.menu_export.addAction(self.action_pyradiomics_export)
        self.menu_export.addAction(self.action_dvh_export)


    def init_windowing_menu(self):
        self.menu_windowing.setIcon(self.icon_windowing)
        self.menu_windowing.setTitle("Windowing")

        dict_windowing = self.patient_dict_container.get("dict_windowing")

        # Get the right order for windowing names
        names_ordered = sorted(dict_windowing.keys())
        if "Normal" in dict_windowing.keys():
            old_index = names_ordered.index("Normal")
            names_ordered.insert(0, names_ordered.pop(old_index))

        # Create actions for each windowing item
        for name in names_ordered:
            text = str(name)
            print(text)
            action_windowing_item = QtWidgets.QAction()
            action_windowing_item.triggered.connect(
                lambda state, text=name: self.action_handler.windowing_handler(state, text)
            )
            action_windowing_item.setText(text)
            self.menu_windowing.addAction(action_windowing_item)


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

    def export_dvh_handler(self):
        if self.patient_dict_container.has_attribute("raw_dvh"):
            self.main_page.dvh_tab.export_csv()
        else:
            QtWidgets.QMessageBox.information(self.main_page,
                                              "Unable to export DVH",
                                              "DVH cannot be exported as there is no DVH present.",
                                              QtWidgets.QMessageBox.Ok)

    def action_exit_handler(self):
        sys.exit()
