from PySide6 import QtWidgets, QtCore

class TransformMatrixDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transformation Matrix (4x4)")
        self.resize(400, 200)

        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(4, 4)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Initialize with identity matrix
        self._init_identity_matrix()

    def _init_identity_matrix(self):
        identity = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        for i in range(4):
            for j in range(4):
                item = QtWidgets.QTableWidgetItem(f"{identity[i][j]:.2f}")
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(i, j, item)

    def set_matrix(self, vtk_transform):
        mat = vtk_transform.GetMatrix()
        for i in range(4):
            for j in range(4):
                item = QtWidgets.QTableWidgetItem(f"{mat.GetElement(i,j):.2f}")
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(i, j, item)
