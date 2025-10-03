from PySide6 import QtWidgets, QtCore

class TransformMatrixDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transformation Matrix")

        # Restore default dialog margins for padding
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.table = QtWidgets.QTableWidget(4, 4)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.table)

        # Set a minimum cell size for better readability
        self._cell_width = 80
        self._cell_height = 32

        # Initialize with identity matrix
        self._init_identity_matrix()

        # Resize to fit table exactly
        self._resize_to_table()

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
        self._resize_to_table()

    def set_matrix(self, mat):
        self._current_matrix = mat
        for i in range(4):
            for j in range(4):
                value = float(mat[i, j]) if hasattr(mat, "__getitem__") else mat.GetElement(i, j)
                item = QtWidgets.QTableWidgetItem(f"{value:.5f}")
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(i, j, item)
        self._resize_to_table()

    def _resize_to_table(self):
        # Set a minimum size for each cell for readability
        for col in range(self.table.columnCount()):
            self.table.setColumnWidth(col, self._cell_width)
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, self._cell_height)
        width = self.table.verticalHeader().width() + sum(
            self.table.columnWidth(i) for i in range(self.table.columnCount())
        )
        height = self.table.horizontalHeader().height() + sum(
            self.table.rowHeight(i) for i in range(self.table.rowCount())
        )

        self.table.setFixedSize(width, height)
        # Let the dialog size to its layout (with padding)
        self.setFixedSize(self.sizeHint())