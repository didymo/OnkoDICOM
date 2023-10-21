from src.View.ImageFusion.ImageFusionAxialView import ImageFusionAxialView
from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtWidgets import QStackedWidget

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Controller.PathHandler import resource_path
from src.View.WindowingUI import Windowing
from src.Model.Windowing import windowing_model


class ActionHandler:
    """
    This class is responsible for initializing all of the actions that
    will be used by the MainPage and its components. There exists a
    1-to-1 relationship between this class and the MainPage. This class
    has access to the main page's attributes and components, however
    this access should only be used to provide functionality to the
    actions defined below. The instance of this class can be given to
    the main page's components in order to trigger actions.
    """

    def __init__(self, main_page):
        self.__main_page = main_page
        self.patient_dict_container = PatientDictContainer()
        self.is_four_view = False
        self.has_image_registration_single = False
        self.has_image_registration_four = False

        ##############################
        # Init all actions and icons #
        ##############################

        # Open patient
        self.icon_open = QtGui.QIcon()
        self.icon_open.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/open_patient_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On)
        self.action_open = QtGui.QAction()
        self.action_open.setIcon(self.icon_open)
        self.action_open.setText("Open new patient")
        self.action_open.setIconVisibleInMenu(True)

        # Save RTSTRUCT changes action
        self.icon_save_structure = QtGui.QIcon()
        self.icon_save_structure.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/save_all_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_save_structure = QtGui.QAction()
        self.action_save_structure.setIcon(self.icon_save_structure)
        self.action_save_structure.setText("Save RTSTRUCT changes")
        self.action_save_structure.setIconVisibleInMenu(True)
        self.action_save_structure.triggered.connect(self.save_struct_handler)

        # Save as Anonymous Action
        self.icon_save_as_anonymous = QtGui.QIcon()
        self.icon_save_as_anonymous.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/anonlock_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_save_as_anonymous = QtGui.QAction()
        self.action_save_as_anonymous.setIcon(self.icon_save_as_anonymous)
        self.action_save_as_anonymous.setText("Save as Anonymous")
        self.action_save_as_anonymous.triggered.connect(
            self.anonymization_handler)

        # Exit action
        self.action_exit = QtGui.QAction()
        self.action_exit.setText("Exit")
        self.action_exit.triggered.connect(self.action_exit_handler)

        # Zoom Out Action
        self.icon_zoom_out = QtGui.QIcon()
        self.icon_zoom_out.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/zoom_out_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_out = QtGui.QAction()
        self.action_zoom_out.setIcon(self.icon_zoom_out)
        self.action_zoom_out.setIconVisibleInMenu(True)
        self.action_zoom_out.setText("Zoom Out")
        self.action_zoom_out.triggered.connect(self.zoom_out_handler)

        # Zoom In Action
        self.icon_zoom_in = QtGui.QIcon()
        self.icon_zoom_in.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/zoom_in_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_zoom_in = QtGui.QAction()
        self.action_zoom_in.setIcon(self.icon_zoom_in)
        self.action_zoom_in.setIconVisibleInMenu(True)
        self.action_zoom_in.setText("Zoom In")
        self.action_zoom_in.triggered.connect(self.zoom_in_handler)

        # Transect Action
        self.icon_transect = QtGui.QIcon()
        self.icon_transect.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/transect_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_transect = QtGui.QAction()
        self.action_transect.setIcon(self.icon_transect)
        self.action_transect.setIconVisibleInMenu(True)
        self.action_transect.setText("Transect")
        self.action_transect.triggered.connect(self.transect_handler)

        # Add-On Options Action
        self.icon_add_ons = QtGui.QIcon()
        self.icon_add_ons.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/management_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_add_ons = QtGui.QAction()
        self.action_add_ons.setIcon(self.icon_add_ons)
        self.action_add_ons.setIconVisibleInMenu(True)
        self.action_add_ons.setText("Add-On Options")
        self.action_add_ons.triggered.connect(self.add_on_options_handler)

        # Switch to Single View Action
        self.icon_one_view = QtGui.QIcon()
        self.icon_one_view.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/axial_view_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_one_view = QtGui.QAction()
        self.action_one_view.setIcon(self.icon_one_view)
        self.action_one_view.setIconVisibleInMenu(True)
        self.action_one_view.setText("One View")
        self.action_one_view.triggered.connect(self.one_view_handler)

        # Switch to 4 Views Action
        self.icon_four_views = QtGui.QIcon()
        self.icon_four_views.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/four_views_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_four_views = QtGui.QAction()
        self.action_four_views.setIcon(self.icon_four_views)
        self.action_four_views.setIconVisibleInMenu(True)
        self.action_four_views.setText("Four Views")
        self.action_four_views.triggered.connect(self.four_views_handler)

        # Show cut lines
        self.icon_cut_lines = QtGui.QIcon()
        self.icon_cut_lines.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/cut_line_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_show_cut_lines = QtGui.QAction()
        self.action_show_cut_lines.setIcon(self.icon_cut_lines)
        self.action_show_cut_lines.setIconVisibleInMenu(True)
        self.action_show_cut_lines.setText("Show Cut Lines")
        self.action_show_cut_lines.triggered.connect(self.cut_lines_handler)

        # Export Pyradiomics Action
        self.action_pyradiomics_export = QtGui.QAction()
        self.action_pyradiomics_export.setText("Export Pyradiomics")
        self.action_pyradiomics_export.triggered.connect(
            self.pyradiomics_export_handler)

        # Export DVH Action
        self.action_dvh_export = QtGui.QAction()
        self.action_dvh_export.setText("Export DVH")
        self.action_dvh_export.triggered.connect(self.export_dvh_handler)

        # Create Windowing menu
        self.icon_windowing = QtGui.QIcon()
        self.icon_windowing.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/windowing_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.menu_windowing = QtWidgets.QMenu()
        self.init_windowing_menu()

        self.windowing_window = Windowing(self)
        self.windowing_window.done_signal.connect(self.update_views)

        # Create Export menu
        self.icon_export = QtGui.QIcon()
        self.icon_export.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/export_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.menu_export = QtWidgets.QMenu()
        self.menu_export.setTitle("Export")
        self.menu_export.addAction(self.action_pyradiomics_export)
        self.menu_export.addAction(self.action_dvh_export)

        # Image Fusion Action
        self.icon_image_fusion = QtGui.QIcon()
        self.icon_image_fusion.addPixmap(
            QtGui.QPixmap(resource_path(
                "res/images/btn-icons/image_fusion_purple_icon.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.action_image_fusion = QtGui.QAction()
        self.action_image_fusion.setIcon(self.icon_image_fusion)
        self.action_image_fusion.setIconVisibleInMenu(True)
        self.action_image_fusion.setText("Image Fusion")

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
        def generate_triggered_handler(text_):
            def handler(state):
                self.windowing_handler(state, text_)

            return handler

        windowing_actions = []
        for name in names_ordered:
            text = str(name)
            action_windowing_item = QtGui.QAction(self.menu_windowing)
            action_windowing_item.triggered.connect(
                generate_triggered_handler(text))
            action_windowing_item.setText(text)
            windowing_actions.append(action_windowing_item)

        # For reasons beyond me, the actions have to be set as a child
        # of the windowing menu *and* later be added to the menu as
        # well. You can't do one or the other, otherwise the menu won't
        # populate. Feel free to try fix (or at least explain why the
        # action has to be set as the windowing menu's child twice)
        for item in windowing_actions:
            self.menu_windowing.addAction(item)

    def save_struct_handler(self):
        """
        If there are changes to the RTSTRUCT detected,
        save the changes to disk.
        """
        if self.patient_dict_container.get("rtss_modified"):
            self.__main_page.structures_tab.save_new_rtss_to_fixed_image_set()
        else:
            QtWidgets.QMessageBox.information(
                self.__main_page, "File not saved",
                "No changes to the RTSTRUCT file detected.")

    def zoom_out_handler(self):
        self.__main_page.zoom_out(self.is_four_view,
                                  self.has_image_registration_single,
                                  self.has_image_registration_four)

    def zoom_in_handler(self):
        self.__main_page.zoom_in(self.is_four_view,
                                 self.has_image_registration_single,
                                 self.has_image_registration_four)

    def windowing_handler(self, state, text):
        """
        Function triggered when a window is selected from the menu.
        :param state: Variable not used. Present to be able to use a
            lambda function.
        :param text: The name of the window selected.
        """
        ptct = PTCTDictContainer()
        mvd = MovingDictContainer()
        if ptct.is_empty() and mvd.is_empty():
            windowing_model(text, [True, False, False, False])
            self.update_views()
        else:
            self.windowing_window.set_window(text)
            self.windowing_window.show()

    def update_views(self):
        """
        function to update all dicom views
        """
        self.__main_page.update_views(update_3d_window=True)

    def anonymization_handler(self):
        """
        Function triggered when the Anonymization button is pressed from
        the menu.
        """

        save_reply = QtWidgets.QMessageBox.information(
            self.__main_page.main_window_instance,
            "Confirmation",
            "Are you sure you want to perform anonymization?",
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )

        if save_reply == QtWidgets.QMessageBox.Yes:
            raw_dvh = self.patient_dict_container.get("raw_dvh")
            hashed_path = self.__main_page.call_class.run_anonymization(
                raw_dvh)
            self.patient_dict_container.set("hashed_path", hashed_path)
            # now that the radiomics data can just get copied across...
            # maybe skip this?
            radiomics_reply = QtWidgets.QMessageBox.information(
                self.__main_page.main_window_instance,
                "Confirmation",
                "Anonymization complete. Would you like to perform radiomics?",
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No
            )
            if radiomics_reply == QtWidgets.QMessageBox.Yes:
                self.__main_page.pyradi_trigger.emit(
                    self.patient_dict_container.path,
                    self.patient_dict_container.filepaths,
                    hashed_path
                )

    def transect_handler(self):
        """
        Function triggered when the Transect button is pressed from the
        menu.
        """
        if hasattr(self.__main_page, 'draw_roi') and self.__main_page.draw_roi:
            self.__main_page.draw_roi.transect_handler()
        else:
            if self.is_four_view:
                view = self.__main_page.dicom_axial_view.view
                slider_id = self.__main_page.dicom_axial_view.slider.value()
            else:
                view = self.__main_page.dicom_single_view.view
                slider_id = self.__main_page.dicom_single_view.slider.value()
            dt = self.patient_dict_container.dataset[slider_id]
            row_s = dt.PixelSpacing[0]
            col_s = dt.PixelSpacing[1]
            dt.convert_pixel_data()
            pixmap = self.patient_dict_container.get("pixmaps_axial")[slider_id]
            self.__main_page.call_class.run_transect(
                self.__main_page,
                view,
                pixmap,
                dt._pixel_array.transpose(),
                row_s,
                col_s
            )

    def add_on_options_handler(self):
        self.__main_page.add_on_options_controller.show_add_on_options()

    def one_view_handler(self):
        self.is_four_view = False

        self.__main_page.dicom_view.setCurrentWidget(
            self.__main_page.dicom_single_view_widget)
        self.__main_page.dicom_single_view.update_view()
        self.__main_page.dicom_single_view_layout.addWidget(
            self.__main_page.windowing_slider, 0, 0)
        self.__main_page.windowing_slider.set_dicom_view(
            self.__main_page.dicom_single_view)

        if hasattr(self.__main_page, 'image_fusion_view'):
            self.has_image_registration_four = False
            self.has_image_registration_single = True
            if isinstance(self.__main_page.image_fusion_single_view,
                          ImageFusionAxialView):
                self.__main_page.image_fusion_view.setCurrentWidget(
                    self.__main_page.image_fusion_single_view)
                self.__main_page.image_fusion_single_view.update_view()

    def four_views_handler(self):
        self.is_four_view = True

        self.__main_page.dicom_view.setCurrentWidget(
            self.__main_page.dicom_four_views_slider)
        self.__main_page.dicom_axial_view.update_view()
        self.__main_page.dicom_four_views_slider_layout.addWidget(
            self.__main_page.windowing_slider, 0, 0)
        self.__main_page.windowing_slider.set_dicom_view(
            self.__main_page.dicom_axial_view)

        if hasattr(self.__main_page, 'image_fusion_view'):
            self.has_image_registration_four = True
            self.has_image_registration_single = False
            if isinstance(self.__main_page.image_fusion_view,
                          QStackedWidget):
                self.__main_page.image_fusion_view.setCurrentWidget(
                    self.__main_page.image_fusion_four_views)
                self.__main_page.image_fusion_view_axial.update_view()

    def cut_lines_handler(self):
        self.__main_page.toggle_cut_lines()

    def export_dvh_handler(self):
        if self.patient_dict_container.has_attribute("raw_dvh"):
            self.__main_page.dvh_tab.export_csv()
        else:
            QtWidgets.QMessageBox.information(
                self.__main_page,
                "Unable to export DVH",
                "DVH cannot be exported as there is no DVH present.",
                QtWidgets.QMessageBox.Ok)

    def pyradiomics_export_handler(self):
        self.__main_page.pyradi_trigger.emit(
            self.patient_dict_container.path,
            self.patient_dict_container.filepaths,
            '')

    def action_exit_handler(self):
        QtCore.QCoreApplication.exit(0)
