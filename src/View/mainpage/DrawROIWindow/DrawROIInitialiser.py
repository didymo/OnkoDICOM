from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QPen, QKeyEvent,QKeySequence, QWheelEvent, QShortcut
from PySide6.QtCore import Qt, Slot
import pydicom
from src.View.mainpage.DrawROIWindow.Toolbar import CutsomToolbar
from src.View.mainpage.DrawROIWindow.ButtonBox import LeftPannel
from src.View.mainpage.DrawROIWindow.Canvas import CanvasLabel
from src.View.mainpage.DrawROIWindow.UnitsBox import UnitsBox
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DrawROIWindow.ScrollLoader import ScrollWheel
from src.View.mainpage.DrawROIWindow.ROINameButton import ROIName
from src.View.mainpage.DrawROIWindow.CopyRoi import CopyROI
from src.View.mainpage.DrawROIWindow.MultiLayerConturePopup import multiPopUp

#Sourcery.ai Is this true
class RoiInitialiser():
    """Class to hold the draw ROI features"""
    def set_up(self, rois, dataset_rtss,signal_roi_drawn,close_window_signal):
        self.signal_roi_drawn = signal_roi_drawn
        self.close_window_signal = close_window_signal
        self.dataset_rtss = dataset_rtss
        self.p = PatientDictContainer()
        self.display_pixmaps = []
        self.zoom_variable = 1.00
        self.get_pixmaps()
        self.setup_ui()
        self.build_toolbar()

    def onZoomInClicked(self):
        """
        Handles the event of the zoom in button
        Parms : None
        Return : None
        
        """
        self.zoom_variable *= 1.05
        self.apply_zoom()
    
    def onZoomOutClicked(self):
        """
        Handles the event of the zoom out button
        Parms : None
        Return : None
        """
        self.zoom_variable /= 1.05
        self.apply_zoom()

    def apply_zoom(self):
        """
        Zooms the canvas in or out depending
        Parms : None
        Return : None
        """
        self.view.setTransform(QtGui.QTransform().scale(self.zoom_variable, self.zoom_variable))
        z = self.zoom_variable * 100
        self.label_zoom.setText(f"Zoom: {z:.2f}%")
    
    def transect_handler(self):
        """
        Handles the transect button
        Parms : None
        Return : None
        """
        self.canvas_labal.set_tool(4)

    def close_window(self):
        """
        Closes the window
        """
        self.close_window_signal.emit()
        self.close()

    def update_draw_roi_pixmaps(self):
        """
        updates the draw roi pixmaps
        """
        self.display_pixmaps.clear()
        self.get_pixmaps()
        self.change_image(self.scroller.value())

    def setup_ui(self):
        """
        sets up the ui
        Parms : None
        Return : None
        """

        # Initialize the pen
        self.pen = QPen()
        self.pen.setWidth(6)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.pen.setColor("blue")

        # Initalises the calsses
        self.scroller = ScrollWheel(self.display_pixmaps)
        self.scroller.valueChanged.connect(self.change_image)
        
        # 1) Scene on the view
        self.scene = QtWidgets.QGraphicsScene(self)
        self.label_image_id = QtWidgets.QLabel()
        self.label_image_pos = QtWidgets.QLabel()
        self.label_wl = QtWidgets.QLabel()
        self.label_image_size = QtWidgets.QLabel()
        self.label_zoom = QtWidgets.QLabel()
        self.label_patient_pos = QtWidgets.QLabel()

        # 2) Base image item
        self.image = self.display_pixmaps[self.scroller.value()]

        self.image_item = QtWidgets.QGraphicsPixmapItem(self.image)

        self.image_item.setZValue(0)
        self.scene.addItem(self.image_item)
        self.scene.setSceneRect(QtCore.QRectF(QtCore.QPointF(0,0), self.image.size()))
        self.canvas_labal = CanvasLabel(self.pen,self.scroller,self.dataset_rtss)
        self.scene.addItem(self.canvas_labal)
        self.scene.setSceneRect(self.image_item.boundingRect())

        # 4) Transparent pixmap for drawing
        overlay_pm = QtGui.QPixmap(self.image.size())
        overlay_pm.fill(Qt.transparent)
        self.canvas_labal.setPixmap(overlay_pm)

        # 5) Align & configure
        self.canvas_labal.setPos(self.image_item.pos())
        self.canvas_labal.setZValue(10)
        self.canvas_labal.setAcceptedMouseButtons(Qt.LeftButton)
        self.canvas_labal.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
        self.canvas_labal.setAcceptedMouseButtons(Qt.LeftButton)
        self.canvas_labal.setTransform(QtGui.QTransform())
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.view.setInteractive(True)
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.view.setFrameShadow(QtWidgets.QFrame.Plain)
        self.view.setLineWidth(0)
        self.view.setMidLineWidth(0)
        self.view.viewport().setAutoFillBackground(False)
        self.view.setBackgroundBrush(Qt.NoBrush)
        self.scene.setBackgroundBrush(Qt.black)

        self._hud = QtWidgets.QWidget(self.view.viewport())
        self._hud.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self._hud.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self._hud.setStyleSheet("background: transparent;")

        grid = QtWidgets.QGridLayout(self._hud)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)

        # Reuse your existing labels (no scene parenting)
        for lbl in (self.label_image_id, self.label_image_pos, self.label_wl,
                    self.label_image_size, self.label_zoom, self.label_patient_pos):
            lbl.setStyleSheet("color: white; background: rgba(0,0,0,90); padding: 2px 6px; border-radius: 4px;")
            lbl.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # Place labels into corners/sides of the HUD grid
      

        grid.addWidget(self.label_image_id, 0, 0, Qt.AlignLeft | Qt.AlignTop)
        grid.addWidget(self.label_image_pos, 0, 0, Qt.AlignLeft | Qt.AlignBottom)

        grid.addWidget(self.label_wl,         0, 1, Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(self.label_patient_pos,2, 1, Qt.AlignRight | Qt.AlignBottom)

        grid.addWidget(self.label_image_size, 2, 0, Qt.AlignLeft  | Qt.AlignTop)
        grid.addWidget(self.label_zoom,       2, 0, Qt.AlignLeft | Qt.AlignBottom)

        # Size the HUD to cover the whole viewport
        self._hud.setGeometry(self.view.viewport().rect())

        # Keep HUD sized when the view resizes
        self.view.viewport().installEventFilter(self)

        self.update_metadata()
        

        self.units_box = UnitsBox(self, self.pen, self.canvas_labal)
        self.left_label = LeftPannel(self, self.pen, self.canvas_labal)
        self.ROI_button = ROIName(self,roi_name="Select ROI")

        # Creates a layout for the tools to fit insid
        tools_layout = QtWidgets.QVBoxLayout()
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(0)                    
        tools_layout.setAlignment(Qt.AlignTop)
        tools_container = QtWidgets.QWidget()
        tools_container.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        tools_container.setLayout(tools_layout)
        tools_layout.addWidget(self.ROI_button)
        tools_layout.addWidget(self.left_label)
        tools_layout.addWidget(self.units_box)
        tools_layout.addStretch(1)
        # Create a layout to hold the left panel and the main canvas
        # Create a QWidget to hold both the left panel and the central label
        # Add the left panel to the layout
        # Add the canvas label to the layout
        # Set the central widget to be our layout container
        central = self.centralWidget() if isinstance(self, QtWidgets.QMainWindow) else self
        main = QtWidgets.QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(8)
        main.addWidget(tools_container)
        main.addWidget(self.scroller)
        main.addWidget(self.view)

        # keep a toolbar factory if you like (QMainWindow will add it)
        self._toolbar = CutsomToolbar(self, self.canvas_labal, self.left_label)
        self.addToolBar(self._toolbar)
        self._toolbar.colour.connect(self.left_label.update_colour)
        self.canvas_labal.emitter.rtss_for_saving.connect(self.saved_roi_drawing)
        self.units_box.opasity_value.connect(self.left_label.update_opasity)
        self.units_box.update_cursor_size.connect(self.left_label.update_cursor)

    def build_toolbar(self) -> QtWidgets.QToolBar:
        """
        Creates and adds the toolbar to the ui
        Parms : None
        Return : QtWidgets.QToolBar
        """
        return self._toolbar

    def get_pixmaps(self):
        """
        Gets all of the pixmap data and returns it
        Parm : None
        Return : None
        """
        pixmaps = self.p.get("pixmaps_axial")
        i = len(pixmaps)
        for j in range(i):
            self.display_pixmaps.append(pixmaps[j])
            
    def change_image(self, v):
        """
        Changes the image (patient image) according to the value
        Parm : None
        Return : None
        """
        image = self.display_pixmaps[v]
        self.image_item.setPixmap(image)
        self.update_metadata()

    def update_metadata(self):
        """
        Update metadata displayed on the DICOM Image view.
        """
        # Retrieve dictionary from the dataset of the slice
        id = self.scroller.value()
        dataset = self.p.dataset[id]

        # Set margin for axial view


        # Information to display
        self.current_slice_number = dataset['InstanceNumber'].value
        total_slices = len(self.p.get("pixmaps_axial"))
        row_img = dataset['Rows'].value
        col_img = dataset['Columns'].value
        window = self.p.get("window")
        level = self.p.get("level")
        slice_pos = dataset['ImagePositionPatient'].value[2]

        if hasattr(dataset, 'PatientPosition'):
            patient_pos = dataset['PatientPosition'].value
            self.label_patient_pos.setText(
                "Patient Position: %s" % (str(patient_pos)))

        # Update labels
        self.label_image_id.setText(
            "Image: %s / %s" % (str(self.current_slice_number), str(total_slices)))
        self.label_image_pos.setText("Position: %s mm" % (str(slice_pos)))
        self.label_wl.setText("W/L: %s/%s" % (str(window), str(level)))
        self.label_image_size.setText(
            "Image Size: %sx%spx" % (str(row_img), str(col_img)))
        z = self.zoom_variable * 100
        self.label_zoom.setText(f"Zoom: {z:.2f}%")

    def close_roi_window(self):
        """Closes the roi window"""
        self._toolbar.close()

    def copy_roi(self):
        """
        Allows the ablity to copy ROIs onto different areas and handles the popups
        Parm : None
        Return : None
        """
        self.copy_roi_window = CopyROI(self.scroller.maximum(), self.scroller.value())
        self.copy_roi_window.copy_number_high.connect(self.canvas_labal.copy_rois_up)
        self.copy_roi_window.copy_number_low.connect(self.canvas_labal.copy_rois_down)
        self.copy_roi_window.show()

    def multi_popup(self):
        """
        Controls the pop for the multi layer conture
        Parm : None
        Return : None
        """
        self.multi_window = multiPopUp(self.scroller.maximum(), self.scroller.value(),
                                          self.units_box.transparency_slider.value(),
                                           self.units_box.pixel_range_max.value(),
                                           self.units_box.pixel_range_min.value())
        self.multi_window.contour_number.connect(self.canvas_labal.multi_layer_commit)
        self.multi_window.max_range_signal.connect(self.canvas_labal.set_max_pixel_value)
        self.multi_window.min_range_signal.connect(self.canvas_labal.set_min_pixel_value)
        self.multi_window.show()

    def window_pop_up(self):
        """
        Opens the popup
        Parm : None
        Return : None
        """
        QtWidgets.QMessageBox.information(self, "No ROI instance selected",
                    "Please ensure you have selected your ROI instance before saving.")
        
    @Slot(pydicom.Dataset,str)
    def saved_roi_drawing(self,v,name):
        """
        Emits the saved roi drawing
        Parm 
        pydicom.Dataset : v
        str : name
        Return : None
        """
        self.signal_roi_drawn.emit((v,{"draw": name}))
        

        