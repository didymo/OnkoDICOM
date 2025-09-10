from PySide6 import QtWidgets
from PySide6.QtGui import QPen, QKeyEvent
from PySide6.QtCore import Qt
from src.View.mainpage.DrawROIWindow.Toolbar import CutsomToolbar
from src.View.mainpage.DrawROIWindow.Left_P import LeftPannel
from src.View.mainpage.DrawROIWindow.Canvas import CanvasLabel
from src.View.mainpage.DrawROIWindow.Units_Box import UnitsBox
from src.View.mainpage.DicomAxialView import DicomAxialView
from src.View.StyleSheetReader import StyleSheetReader


#Sourcery.ai Is this true
class RoiInitialiser(QtWidgets.QWidget):
    """Class to hold the draw ROI features"""
    def __init__(self, host_main_window: QtWidgets.QMainWindow, rois, dataset_rtss, parent=None):
        super().__init__(parent)
        self.host = host_main_window
        self.central = QtWidgets
        self.setWindowTitle("ROI Prototype")
        print("1")

        # Temporary hard coded directory path
        self.last_point = None

        # Initialize the pen
        self.pen = QPen()
        self.pen.setWidth(6)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.pen.setColor("blue")

        # Initalises the calsses
        self.dicom_viewer = DicomAxialView(is_four_view=True)
        self.canvas_labal = CanvasLabel(self.pen)
        self.units_box = UnitsBox(self, self.pen, self.canvas_labal)
        self.left_label = LeftPannel(self, self.pen, self.canvas_labal)
        toolbar = CutsomToolbar(self,self.canvas_labal,self.left_label)

       #Connecting slots & signals
        toolbar.colour.connect(self.left_label.update_colour)

        #Drawing Widget
        drawing_widget = QtWidgets.QWidget()
        drawing_widget.setFixedSize(512,512)

        self.dicom_viewer.setParent(drawing_widget)
        self.dicom_viewer.setGeometry(0,0,512,512)
      
        self.canvas_labal.setParent(drawing_widget)
        self.canvas_labal.setGeometry(0,0,512,512)
        self.canvas_labal.raise_()

        if self.dicom_viewer.layout():
            self.dicom_viewer.layout().setContentsMargins(0, 0, 0, 0)
            self.dicom_viewer.layout().setSpacing(0)

        # Creates a layout for the tools to fit inside
        tools_layout = QtWidgets.QVBoxLayout()
        tools_container = QtWidgets.QWidget()
        tools_container.setLayout(tools_layout)
        tools_layout.addWidget(self.left_label)
        tools_layout.addWidget(self.units_box)

        # Create a layout to hold the left panel and the main canvas
        main_layout = QtWidgets.QHBoxLayout()

        # Create a QWidget to hold both the left panel and the central label
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)

        # Add the left panel to the layout
        main_layout.addWidget(tools_container)
        
        # Add the canvas label to the layout
        main_layout.addWidget(drawing_widget)

        # Set the central widget to be our layout container
        main = QtWidgets.QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(8)
        main.addWidget(tools_container)
        main.addWidget(drawing_widget, 1)

        # keep a toolbar factory if you like (QMainWindow will add it)
        self._toolbar = CutsomToolbar(self, self.canvas_labal, self.left_label)
        self._toolbar.colour.connect(self.left_label.update_colour)

    def build_toolbar(self) -> QtWidgets.QToolBar:
        return self._toolbar
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            self.dicom_viewer.slider.setValue(self.dicom_viewer.slider.value() +1)
            self.canvas_labal.ds_is_active = False
        if event.key() == Qt.Key_Down:
            self.dicom_viewer.slider.setValue(self.dicom_viewer.slider() -1)
            self.canvas_labal.ds_is_active = False
        return super().keyPressEvent(event)