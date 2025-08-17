from PySide6 import QtWidgets, QtCore

from src.View.mainpage.DicomView import DicomView, GraphicsScene


class ImageFusionAxialView(DicomView):
    def __init__(self, roi_color=None,
                 iso_color=None,
                 metadata_formatted=False,
                 cut_line_color=None):
        """
        metadata_formatted: whether the metadata needs to be formatted 
        (only metadata in the four view need to be formatted)
        """
        self.slice_view = 'axial'
        self.metadata_formatted = metadata_formatted
        super(ImageFusionAxialView, self).__init__(roi_color,
                                                   iso_color,
                                                   cut_line_color)

        # Init metadata widgets
        self.metadata_layout = QtWidgets.QVBoxLayout(self.view)
        self.label_image_id = QtWidgets.QLabel()
        self.label_image_pos = QtWidgets.QLabel()
        self.label_wl = QtWidgets.QLabel()
        self.label_image_size = QtWidgets.QLabel()
        self.label_zoom = QtWidgets.QLabel()
        self.label_patient_pos = QtWidgets.QLabel()
        self.init_metadata()

        self.update_view()

    def init_metadata(self):
        """
        Create and place metadata on the view widget.
        """
        # Position of the labels on the DICOM view.
        self.label_image_id.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)
        self.label_image_pos.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)
        self.label_wl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignRight)
        self.label_image_size.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)
        self.label_zoom.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)
        self.label_patient_pos.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignRight)

        # Set all labels to white
        stylesheet = "QLabel { color : white; font-size: 10px;}"
        self.format_metadata_labels(stylesheet)

        # Create a widget to contain the two top-left labels
        top_left_widget = QtWidgets.QWidget()
        top_left = QtWidgets.QVBoxLayout(top_left_widget)
        top_left.addWidget(self.label_image_id,
                           QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)
        top_left.addWidget(self.label_image_pos,
                           QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)

        # Create a widget to contain the top-right label
        top_right_widget = QtWidgets.QWidget()
        top_right = QtWidgets.QVBoxLayout(top_right_widget)
        top_right.addWidget(
            self.label_wl, QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)

        # Create a widget to contain the two top widgets
        top_widget = QtWidgets.QWidget()
        top = QtWidgets.QHBoxLayout(top_widget)
        # Set margin for axial view
        if self.metadata_formatted:
            top_widget.setFixedHeight(50)
            top_widget.setContentsMargins(0, 0, 0, 0)
            top.setContentsMargins(0, 0, 0, 0)
            top.setSpacing(0)
        else:
            top_widget.setFixedHeight(100)
        top.addWidget(top_left_widget, QtCore.Qt.AlignLeft |
                      QtCore.Qt.AlignLeft)
        top.addWidget(top_right_widget, QtCore.Qt.AlignRight |
                      QtCore.Qt.AlignRight)

        # Create a widget to contain the two bottom-left labels
        bottom_left_widget = QtWidgets.QWidget()
        bottom_left = QtWidgets.QVBoxLayout(bottom_left_widget)
        bottom_left.addWidget(self.label_image_size,
                              QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)
        bottom_left.addWidget(
            self.label_zoom, QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)

        # Create a widget to contain the bottom-right label
        bottom_right_widget = QtWidgets.QWidget()
        bottom_right = QtWidgets.QVBoxLayout(bottom_right_widget)
        bottom_right.addWidget(self.label_patient_pos,
                               QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)

        # Create a widget to contain the two bottom widgets
        bottom_widget = QtWidgets.QWidget()
        bottom = QtWidgets.QHBoxLayout(bottom_widget)
        # Set margin for axial view
        if self.metadata_formatted:
            bottom_widget.setFixedHeight(50)
            bottom_widget.setContentsMargins(0, 0, 0, 0)
            bottom.setContentsMargins(0, 0, 0, 0)
            bottom.setSpacing(0)
        else:
            bottom_widget.setFixedHeight(100)
        bottom.addWidget(bottom_left_widget,
                         QtCore.Qt.AlignLeft | QtCore.Qt.AlignLeft)
        bottom.addWidget(bottom_right_widget,
                         QtCore.Qt.AlignRight | QtCore.Qt.AlignRight)

        # Add the bottom and top widgets to the view
        self.metadata_layout.addWidget(
            top_widget, QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)
        self.metadata_layout.addStretch()
        self.metadata_layout.addWidget(
            bottom_widget, QtCore.Qt.AlignBottom | QtCore.Qt.AlignBottom)

    def format_metadata_labels(self, stylesheet):
        """
        Format the meta data's labels
        """
        self.label_image_id.setStyleSheet(stylesheet)
        self.label_image_pos.setStyleSheet(stylesheet)
        self.label_wl.setStyleSheet(stylesheet)
        self.label_image_size.setStyleSheet(stylesheet)
        self.label_zoom.setStyleSheet(stylesheet)
        self.label_patient_pos.setStyleSheet(stylesheet)

    def format_metadata_margin(self):
        """
        Update the margin of the metadata depending on the size of the 
        view and the scene.
        """
        if self.metadata_formatted:
            view_height = self.view.size().height()
            view_width = self.view.size().width()
            scene_height = self.scene.height() * self.zoom
            scene_width = self.scene.width() * self.zoom

            if view_height >= scene_height and view_width >= scene_width:
                # Remove all margin because there is no slider
                self.metadata_layout.setSpacing(0)
                self.metadata_layout.setContentsMargins(0, 0, 0, 0)
            else:
                # Add margin if the vertical and/or horizontal sliders appear
                self.metadata_layout.setSpacing(6)
                if view_height >= scene_height:
                    self.metadata_layout.setContentsMargins(0, 0, 0, 11)
                elif view_width >= scene_width:
                    self.metadata_layout.setContentsMargins(0, 0, 11, 0)
                else:
                    self.metadata_layout.setContentsMargins(0, 0, 11, 11)

    def format_metadata(self, size: QtCore.QSize):
        """
        Update the font size of the meta data's labels depending on the 
        StackedWidget's size.
        :param size: size of the StackedWidget used in the MainPage.
        """
        if self.metadata_formatted:
            # TODO: generalise 1200 and 600
            if size.width() < 1200 and size.height() < 600:
                stylesheet = "QLabel { color : white; font-size: 10px }"
            else:
                stylesheet = "QLabel { color : white; }"
            self.format_metadata_labels(stylesheet)

    def image_display(self, overlay_image=None):
        """
        Update the image to be displayed on the DICOM View.
        If overlay_image is provided, use it as the overlay for this view.
        """
        if overlay_image is not None:
            image = overlay_image
        elif hasattr(self, "overlay_images"):
            slider_id = self.slider.value()
            image = self.overlay_images[slider_id]
        else:
            pixmaps = self.patient_dict_container.get(f"color_{self.slice_view}")
            if pixmaps is None:
                return  # Prevent NoneType subscriptable error
            slider_id = self.slider.value()
            image = pixmaps[slider_id]

        label = QtWidgets.QGraphicsPixmapItem(image)
        self.scene = GraphicsScene(
            label, self.horizontal_view, self.vertical_view)
        
    def update_view(self, zoom_change=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants 
        to change the zoom. False by default.
        """
        super().update_view(zoom_change)
        self.update_metadata()

    def update_metadata(self):
        """
        Update metadata displayed on the DICOM Image view.
        """
        # Retrieve dictionary from the dataset of the slice
        id = self.slider.value()
        dataset = self.patient_dict_container.dataset[id]

        # Set margin for axial view
        self.format_metadata_margin()

        # Information to display
        self.current_slice_number = dataset['InstanceNumber'].value
        total_slices = len(self.patient_dict_container.get("pixmaps_axial"))
        row_img = dataset['Rows'].value
        col_img = dataset['Columns'].value
        window = self.patient_dict_container.get("window")
        level = self.patient_dict_container.get("level")
        slice_pos = dataset['SliceLocation'].value

        if hasattr(dataset, 'PatientPosition'):
            patient_pos = dataset['PatientPosition'].value
            self.label_patient_pos.setText(
                "Patient Position: %s" % (str(patient_pos)))

        # Update labels
        self.label_image_id.setText(
            "Image: %s / %s" % (str(self.current_slice_number),
                                str(total_slices)))
        self.label_image_pos.setText("Position: %s mm" % (str(slice_pos)))
        self.label_wl.setText("W/L: %s/%s" % (str(window), str(level)))
        self.label_image_size.setText(
            "Image Size: %sx%spx" % (str(row_img), str(col_img)))
        self.label_zoom.setText(
            "Zoom: " + "{:.2f}".format(self.zoom * 100) + "%")

    def roi_display(self):
        """
        Display ROI structures on the DICOM Image.
        """
        slider_id = self.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]

        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']
            polygons = self.patient_dict_container.get("dict_polygons_axial")[
                roi_name][curr_slice]
            super().draw_roi_polygons(roi, polygons)
