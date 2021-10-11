import numpy as np
import SimpleITK as sitk

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QIcon, QPixmap

from src.View.resources_open_patient_rc import *

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from src.View.ImageFusion.ManualGraphicsView import GraphicsView

from src.Model.ImageFusion import create_fused_model, get_fused_window

from src.Controller.PathHandler import resource_path
import platform
import math



class UIManualFusionWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        #self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setup_ui()

    def setup_ui(self):
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"


        #initialize containers
        self.patient_dict_container = PatientDictContainer()
        self.moving_dict_container = MovingDictContainer()

        #set window title
        self.setObjectName("Manual Fusion Window")
        self.setWindowTitle("Manual Fusion Window")



        #create button for confirming process completion
        self.confirm_button = QtWidgets.QPushButton()
        self.confirm_button.setText("Confirm")
        self.confirm_button.setObjectName(
            "ConfirmButton")
        self.confirm_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.confirm_button.clicked.connect(self.confirmPressed)


        #initialize position variables
        #self.transform = QtGui.QTransform()
        self.rotation = 0
        self.centre_x = 0
        self.centre_y = 0
        self.offset_y = 0
        self.offset_x = 0

        #create view and sliders
        self.view = GraphicsView(self)
        self.init_view()
        self.scene = QtWidgets.QGraphicsScene()
        self.installEventFilter(self.view)
        self.slider_base = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.slider_move = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.init_sliders()
        
        self.update_image()

        #create layouts for window
        self.manual_layout = QtWidgets.QVBoxLayout()
        self.horizontal_layout = QtWidgets.QHBoxLayout()

        #create widgets to hold layouts
        self.h_display = QtWidgets.QWidget()
        self.v_display = QtWidgets.QWidget()


        self.horizontal_layout.addWidget(self.view)
        self.horizontal_layout.addWidget(self.slider_base)
        self.horizontal_layout.addWidget(self.slider_move)

        self.h_display.setLayout(self.horizontal_layout)

        self.manual_layout.addWidget(self.h_display)
        self.manual_layout.addWidget(self.confirm_button, alignment=QtCore.Qt.AlignRight)
        self.manual_layout.setContentsMargins(0,20,0,0)

        #self.v_display.setLayout(self.manual_layout)

        self.setLayout(self.manual_layout)

        _stylesheet = open(resource_path(self.stylesheet_path)).read()
        self.setStyleSheet(_stylesheet)


    def init_sliders(self):
        """
        Create a slider for the DICOM Image View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps_axial")
        self.slider_base.setMinimum(0)
        self.slider_base.setMaximum(len(pixmaps) - 1)
        self.slider_base.setValue(int(len(pixmaps) / 2))
        self.slider_base.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider_base.setTickInterval(1)

        self.slider_move.setMinimum(0)
        self.slider_move.setMaximum(len(pixmaps) - 1)
        self.slider_move.setValue(int(len(pixmaps) / 2))
        self.slider_move.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider_move.setTickInterval(1)

        self.slider_base.valueChanged.connect(self.update_image)
        self.slider_move.valueChanged.connect(self.update_image)



    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(
            QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)

    def update_image(self):
        pixmaps1 = self.patient_dict_container.get("pixmaps_axial")
        pixmaps2 = self.moving_dict_container.get("pixmaps_axial")

        image1 = pixmaps1[self.slider_base.value()].toImage()
        image2 = pixmaps2[self.slider_move.value()].toImage()


        image2 = image2.convertToFormat(QtGui.QImage.Format_ARGB32)

        self.centre_x = int(image1.width() / 2)
        self.centre_y = int(image1.height() / 2)

        self.transform = QtGui.QTransform()
        self.transform.translate(int(image1.width()/2) + self.offset_x,  \
                                 int(image1.height()/2)+ self.offset_y)
        self.transform.rotate(self.rotation)

        qp = QtGui.QPainter()
        qp.begin(image1)
        qp.setOpacity(0.5)
        qp.setTransform(self.transform)
        qp.drawImage(int(- image2.width()/2), int(-image2.height()/2), image2)
        qp.end()

        pix_item = QtWidgets.QGraphicsPixmapItem(QPixmap.fromImage(image1))
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addItem(pix_item)
        self.view.setScene(self.scene)


    def applyTransform(self, pixmap):
        image = pixmap.toImage()
        image = image.convertToFormat(QtGui.QImage.Format_RGB32)
        background = QtGui.QImage(512, 512, QtGui.QImage.Format_RGB32)
        background.fill(QtGui.QColor("black"))
        qp = QtGui.QPainter()
        qp.begin(background)
        qp.setTransform(self.transform)
        qp.drawImage(int(- image.width()/2), int(-image.height()/2), image)
        qp.end()
        return background



    def mouseMoveEvent(self, event):
        new_x = event.localPos().x()
        new_y = event.localPos().y()

        circle_x = (new_x - self.centre_x) ** 2
        circle_y = (new_y - self.centre_y) ** 2

        x = new_x - self.centre_x
        y = new_y - self.centre_y

        distance = math.sqrt(x ** 2 + y ** 2)
        angle = math.degrees(-math.atan2(y, x))
        self.rotation = -angle

        if event.buttons() and Qt.LeftButton and (circle_x + circle_y < 65536):
            self.update_image()




    def keyPressEvent(self, event):
        if(event.key() == Qt.Key_Up):
            self.offset_y -= 1
            self.update_image()
        if(event.key() == Qt.Key_Down):
            self.offset_y += 1
            self.update_image()
        if(event.key() == Qt.Key_Left):
            self.offset_x -= 1
            self.update_image()
        if(event.key() == Qt.Key_Right):
            self.offset_x += 1
            self.update_image()


    def qimage_to_ndarray(self, image):
        size = image.size()
        buffers = image.constBits()
        n_bits_buffer = len(buffers)*8
        n_bits_image = size.width()*size.height()*image.depth()
        
        array = np.ndarray(shape = (size.height(), size.width()),
                           buffer = buffers,
                           dtype = np.uint8)
        
        return array



    def degrees_to_radians(self, degree):
        return degree*(math.pi/180)


    def transform_array(self, array):
        image = sitk.GetImageFromArray(array)
        transform = sitk.Euler2DTransform()
        transform.SetCenter(image.TransformContinuousIndexToPhysicalPoint(np.array(
            image.GetSize())/2.0))

        transform.SetTranslation((self.offset_x, self.offset_y))
        transform.SetAngle(self.degrees_to_radians(self.rotation))

        transformed_image = sitk.Resample(image, transform)

        return sitk.GetArrayFromImage(transformed_image)


            
    def confirmPressed(self):
        datasets = self.moving_dict_container.dataset

        pixel_spacing = datasets[0].PixelSpacing
        pixel_spacing = np.append(pixel_spacing, datasets[0].SliceThickness)

        #dataset length is 1 more than the index range for itself... weird
        for i in range(0, len(datasets)-1):
            pix_array = datasets[i].pixel_array
            transformed_array = self.transform_array(pix_array)
            if (i == 0):
                np_arrays = np.array([transformed_array])
            else:
                np_arrays = np.append(np_arrays, [transformed_array], axis=0)
        
        sitk_image = sitk.GetImageFromArray(np_arrays, isVector=False)
        sitk_image.SetSpacing(pixel_spacing)
        
        self.moving_dict_container.set("sitk_moving", sitk_image)

        create_fused_model(self.patient_dict_container.get("sitk_original"), sitk_image)


        color_axial, color_sagittal, color_coronal, tfm = get_fused_window(
            self.patient_dict_container.get("level"),self.patient_dict_container.get("window"))

        self.patient_dict_container.set("color_axial", color_axial)
        self.patient_dict_container.set("color_sagittal", color_sagittal)
        self.patient_dict_container.set("color_coronal", color_coronal)
        self.moving_dict_container.set("tfm", tfm)

        self.close()



    def closeEvent(self, event):
        close = QtWidgets.QMessageBox.question(self,
                                     "QUIT",
                                     "Are you sure want to stop manual adjustment?",
                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if close == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
            
            	
                                   
