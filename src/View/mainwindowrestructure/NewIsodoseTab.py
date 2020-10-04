from PyQt5 import QtWidgets, QtGui, QtCore

from src.Model.PatientDictContainer import PatientDictContainer


class NewIsodoseTab(QtWidgets.QWidget):

    request_update_isodoses = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.rxdose = self.patient_dict_container.get("rxdose")
        self.color_dict = self.init_color_isod()
        self.color_squares = self.init_color_squares()
        self.checkboxes = self.init_checkboxes()

        self.isodose_tab_layout = QtWidgets.QVBoxLayout()
        self.isodose_tab_layout.setAlignment(QtCore.Qt.AlignTop)
        self.isodose_tab_layout.setSpacing(0)
        self.init_layout()

        self.setLayout(self.isodose_tab_layout)

    def init_layout(self):
        for i in range(0, len(self.checkboxes)):
            widget_isodose = QtWidgets.QWidget()
            layout_isodose = QtWidgets.QHBoxLayout(widget_isodose)
            layout_isodose.setAlignment(QtCore.Qt.AlignLeft)
            layout_isodose.addWidget(self.color_squares[i])
            layout_isodose.addWidget(self.checkboxes[i])
            self.isodose_tab_layout.addWidget(widget_isodose)

    def init_color_isod(self):
        """
        Create a dictionary containing the colors for each isodose.

        :return: Dictionary where the key is the percentage of isodose and the value a QColor object.
        """
        roi_color = dict()
        roi_color[107] = QtGui.QColor(131, 0, 0)
        roi_color[105] = QtGui.QColor(185, 0, 0)
        roi_color[100] = QtGui.QColor(255, 46, 0)
        roi_color[95] = QtGui.QColor(255, 161, 0)
        roi_color[90] = QtGui.QColor(253, 255, 0)
        roi_color[80] = QtGui.QColor(0, 255, 0)
        roi_color[70] = QtGui.QColor(0, 143, 0)
        roi_color[60] = QtGui.QColor(0, 255, 255)
        roi_color[30] = QtGui.QColor(33, 0, 255)
        roi_color[10] = QtGui.QColor(11, 0, 134)

        return roi_color

    def init_color_squares(self):
        list_of_squares = []
        for key, value in self.color_dict.items():
            list_of_squares.append(self.draw_color_square(value))

        return list_of_squares

    def init_checkboxes(self):
        list_of_checkboxes = []
        # Values of Isodoses
        val1 = int(1.07 * self.rxdose)
        val2 = int(1.05 * self.rxdose)
        val3 = int(1.00 * self.rxdose)
        val4 = int(0.95 * self.rxdose)
        val5 = int(0.90 * self.rxdose)
        val6 = int(0.80 * self.rxdose)
        val7 = int(0.70 * self.rxdose)
        val8 = int(0.60 * self.rxdose)
        val9 = int(0.30 * self.rxdose)
        val10 = int(0.10 * self.rxdose)

        # Checkboxes
        checkbox1 = QtWidgets.QCheckBox("107 % / " + str(val1) + " cGy [Max]")
        checkbox2 = QtWidgets.QCheckBox("105 % / " + str(val2) + " cGy")
        checkbox3 = QtWidgets.QCheckBox("100 % / " + str(val3) + " cGy")
        checkbox4 = QtWidgets.QCheckBox("95 % / " + str(val4) + " cGy")
        checkbox5 = QtWidgets.QCheckBox("90 % / " + str(val5) + " cGy")
        checkbox6 = QtWidgets.QCheckBox("80 % / " + str(val6) + " cGy")
        checkbox7 = QtWidgets.QCheckBox("70 % / " + str(val7) + " cGy")
        checkbox8 = QtWidgets.QCheckBox("60 % / " + str(val8) + " cGy")
        checkbox9 = QtWidgets.QCheckBox("30 % / " + str(val9) + " cGy")
        checkbox10 = QtWidgets.QCheckBox("10 % / " + str(val10) + " cGy")

        checkbox1.clicked.connect(lambda state, text=107: self.checked_dose(state, text))
        checkbox2.clicked.connect(lambda state, text=105: self.checked_dose(state, text))
        checkbox3.clicked.connect(lambda state, text=100: self.checked_dose(state, text))
        checkbox4.clicked.connect(lambda state, text=95: self.checked_dose(state, text))
        checkbox5.clicked.connect(lambda state, text=90: self.checked_dose(state, text))
        checkbox6.clicked.connect(lambda state, text=80: self.checked_dose(state, text))
        checkbox7.clicked.connect(lambda state, text=70: self.checked_dose(state, text))
        checkbox8.clicked.connect(lambda state, text=60: self.checked_dose(state, text))
        checkbox9.clicked.connect(lambda state, text=30: self.checked_dose(state, text))
        checkbox10.clicked.connect(lambda state, text=10: self.checked_dose(state, text))

        checkbox1.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox2.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox3.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox4.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox5.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox6.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox7.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox8.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox9.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox10.setStyleSheet("font: 10pt \"Laksaman\";")

        list_of_checkboxes.append(checkbox1)
        list_of_checkboxes.append(checkbox2)
        list_of_checkboxes.append(checkbox3)
        list_of_checkboxes.append(checkbox4)
        list_of_checkboxes.append(checkbox5)
        list_of_checkboxes.append(checkbox6)
        list_of_checkboxes.append(checkbox7)
        list_of_checkboxes.append(checkbox8)
        list_of_checkboxes.append(checkbox9)
        list_of_checkboxes.append(checkbox10)

        return list_of_checkboxes


    # Function triggered when a dose level selected
    # Updates the list of selected isodoses and dicom view
    def checked_dose(self, state, isod_value):
        """
        Function triggered when the checkbox of a structure is checked / unchecked.
        Update the list of selected structures.
        Update the DICOM view.

        :param state: True if the checkbox is checked, False otherwise.
        :param isod_value: Percentage of isodose.
        """

        selected_doses = self.patient_dict_container.get("selected_doses")

        if state:
            # Add the dose to the list of selected doses
            selected_doses.append(isod_value)
        else:
            # Remove dose from list of previously selected doses
            selected_doses.remove(isod_value)

        self.patient_dict_container.set("selected_doses", selected_doses)

        # Update the dicom view
        self.request_update_isodoses.emit()

    def draw_color_square(self, color):
        """
        Create a color square.
        :param color: QColor object
        :return: Color square widget.
        """
        color_square_label = QtWidgets.QLabel()
        color_square_pix = QtGui.QPixmap(15, 15)
        color_square_pix.fill(color)
        color_square_label.setPixmap(color_square_pix)

        return color_square_label
