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
        
        #remove the scroll bar and add it to its own widget
        self.dicom_viewer.layout().removeWidget(self.dicom_viewer.slider)
        self.dicom_scroller = QtWidgets.QWidget()
        self.dicom_viewer.slider.setParent(self.dicom_scroller)

        scroller_layout = QtWidgets.QVBoxLayout(self.dicom_scroller)
        scroller_layout.setContentsMargins(0, 0, 0, 0)
        scroller_layout.setSpacing(0)

        # 4) reparent + add the slider to the scroller's layout
        scroller_layout.addWidget(self.dicom_viewer.slider)
        self.dicom_viewer.slider.show()

        
        self.canvas_labal = CanvasLabel(self.pen, self.dicom_viewer)
        self.units_box = UnitsBox(self, self.pen, self.canvas_labal)
        self.left_label = LeftPannel(self, self.pen, self.canvas_labal)
        toolbar = CutsomToolbar(self,self.canvas_labal,self.left_label)

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
        # Create a QWidget to hold both the left panel and the central label
        # Add the left panel to the layout
        # Add the canvas label to the layout
        # Set the central widget to be our layout container
        main = QtWidgets.QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(8)
        main.addWidget(tools_container)
        main.addWidget(self.dicom_scroller)
        main.addWidget(drawing_widget, 1)

        # keep a toolbar factory if you like (QMainWindow will add it)
        self._toolbar = CutsomToolbar(self, self.canvas_labal, self.left_label)
        self._toolbar.colour.connect(self.left_label.update_colour)
        print("scroller sizeHint:", self.dicom_scroller.sizeHint())
        print("slider sizeHint:", self.dicom_viewer.slider.sizeHint())

    def build_toolbar(self) -> QtWidgets.QToolBar:
        return self._toolbar
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            self.dicom_viewer.slider.setValue(self.dicom_viewer.slider.value() +1)
            self.canvas_labal.ds_is_active = False
        if event.key() == Qt.Key_Down:
            self.dicom_viewer.slider.setValue(self.dicom_viewer.slider.value() -1)
            self.canvas_labal.ds_is_active = False
        return super().keyPressEvent(event)