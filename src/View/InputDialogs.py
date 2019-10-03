import re
import sys
from PyQt5.QtWidgets import QTableWidgetItem, QLabel, QDialogButtonBox, QVBoxLayout, QFormLayout, QSpinBox, QLineEdit, \
    QDialog, \
    QComboBox, QGroupBox, QMessageBox


class Dialog_Windowing(QDialog):

    def __init__(self, winName,scan,ULevel, LLevel):
        super(Dialog_Windowing, self).__init__()

        self.winName = winName
        self.scan = scan
        self.ULevel = ULevel
        self.LLevel = LLevel
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,self)
        self.name = QLineEdit()
        self.name.setText(self.winName)
        self.sc = QLineEdit()
        self.sc.setText(self.scan)
        self.ul = QLineEdit()
        self.ul.setText(self.ULevel)
        self.ll = QLineEdit()
        self.ll.setText(self.LLevel)

        layout = QFormLayout(self)
        layout.addRow(QLabel("Window Name:"), self.name)
        layout.addRow(QLabel("Scan:"), self.sc)
        layout.addRow(QLabel("Upper Value:"), self.ul)
        layout.addRow(QLabel("Lower Value:"), self.ll)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Image Windowing")


    def getInputs(self):
        return (self.name.text(), self.sc.text(), self.ul.text(),self.ll.text())

    def accepting(self):
        if (self.name.text()!='' and self.sc.text()!='' and self.ul.text()!= '' and self.ll.text()!=''):
            #check validation
            if re.match(r'^([\s\d]+)$', self.ul.text()) and re.match(r'^([\s\d]+)$', self.ll.text()):
               self.accept()
            else:
                buttonReply = QMessageBox.warning(self, "Error Message",
                                              "The level fields need to be numbers!", QMessageBox.Ok)
                if buttonReply == QMessageBox.Ok:
                    pass
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass



class Dialog_Organ(QDialog):

    def __init__(self, Name,id,organ):
        super(Dialog_Organ, self).__init__()

        self.name = Name
        self.id = id
        self.org = organ
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,self)
        self.S_name = QLineEdit()
        self.S_name.setText(self.name)
        self.oID = QLineEdit()
        self.oID.setText(self.id)
        self.organ = QLineEdit()
        self.organ.setText(self.org)


        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.S_name)
        layout.addRow(QLabel("FMA ID:"), self.oID)
        layout.addRow(QLabel("Organ:"), self.organ)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Standard Organ Names")


    def getInputs(self):
        return (self.S_name.text(), self.oID.text(), self.organ.text())

    def accepting(self):
        if (self.S_name.text()!='' and self.oID.text()!='' and self.organ.text()!= '' ):
            #check validation
            if re.match(r'^([\s\d]+)$', self.oID.text()):
               self.accept()
            else:
                buttonReply = QMessageBox.warning(self, "Error Message",
                                              "The FMA ID field should to be a number!", QMessageBox.Ok)
                if buttonReply == QMessageBox.Ok:
                    pass
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass


class Dialog_Volume(QDialog):

    def __init__(self, Name,volume):
        super(Dialog_Volume, self).__init__()

        self.name = Name
        self.vol = volume
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,self)
        self.S_name = QLineEdit()
        self.S_name.setText(self.name)
        self.volume = QLineEdit()
        self.volume.setText(self.vol)

        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.S_name)
        layout.addRow(QLabel("Volume Name:"), self.volume)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Standard Volume Names")


    def getInputs(self):
        return (self.S_name.text(), self.volume.text())

    def accepting(self):
        if (self.S_name.text()!='' and self.volume.text()!=''):
           self.accept()
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass

class Dialog_Dose(QDialog):

    def __init__(self, dose):
        super(Dialog_Dose, self).__init__()

        self.dose = dose
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,self)
        self.iso_dose = QLineEdit()
        self.iso_dose.setText(self.dose)

        layout = QFormLayout(self)
        layout.addRow(QLabel("Isodose Level (cCy):"), self.iso_dose)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Standard Volume Names")


    def getInputs(self):
        return (self.iso_dose.text(), str('ISO' + self.iso_dose.text()))

    def accepting(self):
        if (self.iso_dose.text()!=''):
            if re.match(r'^\d+$', self.iso_dose.text()):
                self.accept()
            else:
                buttonReply = QMessageBox.warning(self, "Error Message",
                                                  "The Isodose level should to be a number!", QMessageBox.Ok)
                if buttonReply == QMessageBox.Ok:
                    pass
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "The field should not be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass