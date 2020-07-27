import csv

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QApplication, QWidget, QHBoxLayout, QPushButton


class RenameROIWindow(QDialog):

    def __init__(self, standard_names, *args, **kwargs):
        super(RenameROIWindow, self).__init__(*args, **kwargs)

        self.standard_names = standard_names

        self.setWindowTitle("Rename Region of Interest")
        self.resize(248, 80)

        self.explanation_text = QLabel("Enter a new name:")

        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self.on_text_edited)

        self.error_text = QLabel()
        self.error_text.setStyleSheet("color: red")

        self.button_area = QWidget()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.rename_button = QPushButton("Rename")
        self.rename_button.setDisabled(True)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.rename_button)
        self.button_area.setLayout(self.button_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.error_text)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

    def on_text_edited(self, text):
        if text in self.standard_names:
            self.error_text.setText("")
            self.rename_button.setDisabled(False)
        else:
            self.error_text.setText("Entered name is not in standard names")
            self.rename_button.setDisabled(True)


if __name__ == "__main__":
    import sys

    standard_names = []
    with open('src/data/csv/organName.csv', 'r') as f:
        csv_input = csv.reader(f)
        header = next(f)
        for row in csv_input:
            standard_names.append(row[0])

    with open('src/data/csv/volumeName.csv', 'r') as f:
        csv_input = csv.reader(f)
        header = next(f)
        for row in csv_input:
            standard_names.append(row[1])

    app = QApplication(sys.argv)
    window = RenameROIWindow(standard_names)
    window.show()
    app.exec_()
