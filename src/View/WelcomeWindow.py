from src.View.OpenPatientWindow import *
from src.Controller.PathHandler import resource_path
import platform


class UIWelcomeWindow(object):

    # the ui constructor function
    def setup_ui(self, welcome_window_instance):
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(QtGui.QPixmap(resource_path("res/images/icon.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off) # adding icon
        welcome_window_instance.setObjectName("WelcomeWindowInstance")
        welcome_window_instance.setWindowIcon(window_icon)
        welcome_window_instance.setFixedSize(840, 530)

        # Set a vertical layout to manage layout in a vertical manner
        self.window_vertical_layout_box = QtWidgets.QVBoxLayout()
        self.window_vertical_layout_box.setObjectName("WindowVerticalLayoutBox")

        # Set up the Logo Holder for the Welcome Window
        self.logo_holder = QtWidgets.QHBoxLayout()
        self.welcome_window_logo = QtWidgets.QLabel()
        self.welcome_window_logo.setPixmap(QtGui.QPixmap(resource_path("res/images/image.png")))
        self.welcome_window_logo.setScaledContents(True)
        self.welcome_window_logo.setObjectName("WelcomeWindowLogo")
        self.welcome_window_logo.setFixedSize(480, 260)
        self.logo_holder.addWidget(self.welcome_window_logo)
        self.window_vertical_layout_box.addStretch(1)
        self.window_vertical_layout_box.addLayout(self.logo_holder)

        # Set up the Label for the Welcome Window
        self.welcome_window_label = QtWidgets.QLabel()
        self.welcome_window_label.setObjectName("WelcomeWindowLabel")
        # welcome_window_label_font = QtGui.QFont(FontService.get_instance().font_family(), 18)
        # welcome_window_label_font.setBold(True)
        # self.welcome_window_label.setFont(welcome_window_label_font)
        self.welcome_window_label.setAlignment(Qt.AlignCenter)
        self.window_vertical_layout_box.addWidget(self.welcome_window_label)

        # Set up the Slogan for the Welcome Window
        self.welcome_window_slogan = QtWidgets.QLabel()
        self.welcome_window_slogan.setObjectName("WelcomeWindowSlogan")
        # welcome_window_slogan_font = QtGui.QFont(FontService.get_instance().font_family(), 12)
        # self.welcome_window_slogan.setFont(welcome_window_slogan_font)
        self.welcome_window_slogan.setAlignment(Qt.AlignCenter)
        self.window_vertical_layout_box.addWidget(self.welcome_window_slogan)

        # button to open a patient
        self.open_patient_button = QtWidgets.QPushButton()
        self.open_patient_button.setObjectName("OpenPatientButton")
        self.open_patient_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_patient_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.open_patient_button.resize(480, 261)

        # Button to start batch processing
        self.open_batch_button = QtWidgets.QPushButton()
        self.open_batch_button.setObjectName("OpenBatchProcessingButton")
        self.open_batch_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_batch_button.setSizePolicy(
            QtWidgets.QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.open_batch_button.resize(480, 261)

        # Setup button layout - empty QLabels to align buttons nicely
        self.buttons_holder = QtWidgets.QGridLayout()
        self.buttons_holder.addWidget(QtWidgets.QLabel(), 1, 0, 1, 1)
        self.buttons_holder.addWidget(self.open_patient_button, 1, 1, 2, 1)
        self.buttons_holder.addWidget(QtWidgets.QLabel(), 1, 3, 1, 1)
        self.buttons_holder.addWidget(QtWidgets.QLabel(), 3, 0, 1, 1)
        self.buttons_holder.addWidget(self.open_batch_button, 3, 1, 2, 1)
        self.buttons_holder.addWidget(QtWidgets.QLabel(), 3, 3, 1, 1)
        self.window_vertical_layout_box.addStretch(1)
        self.window_vertical_layout_box.addLayout(self.buttons_holder)
        self.window_vertical_layout_box.addStretch(1)

        self.welcome_window_instance_central_widget = QtWidgets.QWidget()
        self.welcome_window_instance_central_widget.setLayout(self.window_vertical_layout_box)
        welcome_window_instance.setCentralWidget(self.welcome_window_instance_central_widget)
        welcome_window_instance.setStyleSheet(stylesheet)
        self.retranslate_ui(welcome_window_instance)
        QtCore.QMetaObject.connectSlotsByName(welcome_window_instance)

    # this function inserts all the text in the welcome page
    def retranslate_ui(self, welcome_window_instance):
        _translate = QtCore.QCoreApplication.translate
        welcome_window_instance.setWindowTitle(_translate("WelcomeWindowInstance", "OnkoDICOM"))
        self.welcome_window_label.setText(_translate("WelcomeWindowInstance", "Welcome to OnkoDICOM!"))
        self.welcome_window_slogan.setText(_translate("WelcomeWindowInstance",
                                        "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."))
        self.open_patient_button.setText(_translate("WelcomeWindowInstance", "Individual Patient Curation"))
        self.open_batch_button.setText(_translate("WelcomeWindowInstance",
                                                  "Batch Processing"))
