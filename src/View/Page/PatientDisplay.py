import glob
from src.View.Component.PatientBar import *
from src.View.Component.MenuBar import *

class UI_PatientDisplay(object):

    def setup_ui(self, PatientDisplay):
        """
        IMPLEMENTATION OF THE MAIN PAGE VIEW
        """
        # Main Window
        PatientDisplay.setMinimumSize(1080, 700)
        PatientDisplay.setWindowTitle("OnkoDICOM")
        PatientDisplay.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        "Main Container and Layout"
        self.main_widget = QtWidgets.QWidget(MainWindow)
        self.main_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)

        "Patient Bar"
        self.patient_bar = PatientBar(self)

        """
        Functionality Container and Layout
        (Structure/Isodose tab, Structure Information tab, DICOM View / DVH / DICOM Tree / Clinical Data tab)
        """
        self.function_widget = QtWidgets.QWidget(MainWindow)
        self.function_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.function_layout = QtWidgets.QHBoxLayout(self.function_widget)
        self.function_layout.setContentsMargins(0, 0, 0, 0)

        "Left Column"
        self.left_widget = QtWidgets.QWidget(self.main_widget)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_widget.setMaximumWidth(230)

        "Left Top Column: Structure and Isodoses Tabs"
        self.tab1 = QtWidgets.QTabWidget(self.left_widget)
        self.tab1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab1.setGeometry(QtCore.QRect(0, 40, 200, 361))

        self.left_layout.addWidget(self.tab1)

        "View of DICOM VIEW, DVH, DICOM Tree, Clinical DAta"
        self.tab2 = QtWidgets.QTabWidget(self.main_widget)
        self.tab2.setGeometry(QtCore.QRect(200, 40, 880, 561))
        self.tab2.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

        self.function_layout.addWidget(self.left_widget)
        self.function_layout.addWidget(self.tab2)

        self.main_layout.addWidget(self.function_widget)

        self.tab1.raise_()
        self.tab2.raise_()
        """
        End of Functionality Container and Layout
        """

        "Menu Bar"
        self.menu_bar = MenuBar(PatientDisplay)



        self.create_footer()

        MainWindow.setCentralWidget(self.main_widget)

        self.tab1.setCurrentIndex(0)
        self.tab2.setCurrentIndex(0)

    def create_footer(self):
        # Bottom Layer
        self.bottom_widget = QtWidgets.QWidget(self.main_widget)
        self.hLayout_bottom = QtWidgets.QHBoxLayout(self.bottom_widget)
        self.hLayout_bottom.setContentsMargins(0, 0, 0, 0)

        # Bottom Layer: "@OnkoDICOM_2019" label
        self.label = QtWidgets.QLabel(self.bottom_widget)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet("font: 9pt \"Laksaman\";")
        self.label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label.setText("@OnkoDICOM 2020")

        self.hLayout_bottom.addWidget(self.label)

        self.main_layout.addWidget(self.bottom_widget)
        self.bottom_widget.raise_()

    def loadData(self, path, dataset, filepaths, rois, raw_dvh, dvhxy, raw_contour, nnum_points, pixluts):
        """
        IMPLEMENTATION OF THE MAIN PAGE VIEW
        """
        self.dataset = dataset
        self.raw_dvh = raw_dvh
        self.dvh_x_y = dvhxy

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UI_PatientDisplay()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())