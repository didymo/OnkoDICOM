from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class TransectWindow(QWidget):
    """Class to display the transect graph"""
    def __init__(self, hu_values = []):
        super().__init__()
        self.hu = hu_values
        self.setWindowTitle("Transect Graph")
        self.resize(533,300)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.plot()

    def plot(self):
        ax = self.figure.add_subplot(111)
        ax.plot(range(len(self.hu)), self.hu)
        ax.set_xlabel("HU values")
        ax.set_title("Transected Plot")
        self.canvas.draw()

