from PySide6 import QtWidgets
from typing import Optional
from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton, QButtonGroup, QMessageBox
from PySide6.QtGui import QPixmap, QPixmap, QPainter, QPen, QColor,QCursor
from PySide6.QtCore import Qt, Slot, Signal

class LeftPannel(QtWidgets.QWidget):
    """Holds the left pannels buttons"""
    def __init__(self, parent = None, pen = None, canvas_label = None):
        super().__init__(parent)
        self.canvas_label = canvas_label
        self.parent = parent
        self.pen = pen
        self.last_colour = QColor("blue")
        self.last_colour.setAlpha(126)
        self.was_erasor = False
        self.set_layout()

    def set_layout(self):
        """Fucntion to set the buttons layout"""
        #Initalises the buttons
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self._grid_group_box = QGroupBox()
        layout = QGridLayout()
        brush = QPushButton("Brush")
        brush.setCheckable(True)
        pen = QPushButton("Pen")
        pen.setCheckable(True)
        eraser_roi = QPushButton("Trim ROI")
        eraser_roi.setCheckable(True)
        eraser_draw = QPushButton("Remove ROI")
        transect = QPushButton("Transect")
        transect.setCheckable(True)
        copy = QPushButton("Copy ROI")
        save = QPushButton("Save")
        fill = QPushButton("Fill")
        fill.setCheckable(True)
        multi = QPushButton("Multi")
        erase_dag = QPushButton("Erase DAGs")
        cancel = QPushButton("Cancel")
        self.button_group.addButton(brush)
        self.button_group.addButton(pen)
        self.button_group.addButton(eraser_draw)
        self.button_group.addButton(eraser_roi)
        self.button_group.addButton(transect)
        self.button_group.addButton(copy)
        self.button_group.addButton(save)
        self.button_group.addButton(fill)
        self.button_group.addButton(erase_dag)
        self.button_group.addButton(multi)
        self.button_group.addButton(cancel)

        #Links the buttons to actions
        brush.clicked.connect(self.brush_tool)
        pen.clicked.connect(self.pen_tool)
        eraser_roi.clicked.connect(self.eraser_roi_tool)
        eraser_draw.clicked.connect(self.eraser_draw_tool)
        transect.clicked.connect(self.transect_tool)
        copy.clicked.connect(self.copy_button)
        save.clicked.connect(self.save_button)
        fill.clicked.connect(self.fill_tool)
        erase_dag.clicked.connect(self.canvas_label.erase_dags)
        multi.clicked.connect(self.multi_button)
        cancel.clicked.connect(self.cancel_button)

        #Sets the buttons in the layout 2 by 3
        layout.addWidget(brush,0,0)
        layout.addWidget(pen, 0,1)
        layout.addWidget(eraser_roi,1,0)
        layout.addWidget(eraser_draw,1,1)
        layout.addWidget(multi,2,0)
        layout.addWidget(fill, 2,1)
        layout.addWidget(copy,3,0)
        layout.addWidget(transect,4,0)
        layout.addWidget(erase_dag, 4,1)
        layout.addWidget(save,5,0)
        layout.addWidget(cancel,5,1)
        
        

        #adds the layout to the grid_group_box
        #Bundles everything up yay!
        self._grid_group_box.setLayout(layout)
        main_layout = QtWidgets.QVBoxLayout()  # Create main layout for the left panel
        main_layout.addWidget(self._grid_group_box)  # Add the group box to the main layout
        self.setLayout(main_layout)  # Set th
        
    def brush_tool(self):
        """This fucntion changes the draw tool to a brush"""
        self.canvas_label.set_tool(1)
        self.canvas_label.pen.setColor(self.last_colour)
        cursor = self.make_circle_cursor(self.canvas_label.pen.width(), self.last_colour)
        self.canvas_label.setCursor(cursor)
        self.was_erasor = False

    def pen_tool(self):
        """This fucntion changes the draw tool to a pen"""
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(3)
        self.canvas_label.setCursor(Qt.CrossCursor)

    def eraser_roi_tool(self):
        """This fucntion changes the draw tool to the eraser ROI tool"""
        self.canvas_label.set_tool(1)
        cursor = self.make_circle_cursor(self.canvas_label.pen.width(),\
                                         QColor(Qt.black), fill=QColor(Qt.white))
        self.canvas_label.setCursor(cursor)
        self.canvas_label.pen.setColor(Qt.transparent)
        self.was_erasor = True

    def eraser_draw_tool(self):
        """This fucntion changes the draw tool to a eraser draw tool"""
        self.canvas_label.erase_roi()

    def transect_tool(self):
        """This fucntion activates the transect tool"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.set_tool(4)

    def copy_button(self):
        """This fucntion activates the copy pop up window"""
        self.parent.copy_roi()

    def save_button(self):
        """This fucntion saves the ROI drawing"""
        if self.canvas_label.roi_name is None:
            self.parent.window_pop_up()
        else:
            self.canvas_label.save_roi()
            self.parent.close_window()

    def multi_button(self):
        """This fucntion calls the multi putton"""
        self.parent.multi_popup()

    def fill_tool(self):
        """Fucntion for the fill tool"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(2)

    def cancel_button(self):
        """This fucntion saves the ROI drawing"""
        if len(self.canvas_label.has_been_draw_on) > 0:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Cancel Drawing?")
            dlg.setText("Are you sure you want to exit? If you cancel the ROI will not be saved")
            dlg.setIcon(QMessageBox.Critical)
            dlg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            dlg.setDefaultButton(QMessageBox.Retry)
            choice = dlg.exec()
            if choice == QMessageBox.Ok:
                self.parent.close_window()
            if choice == QMessageBox.Cancel:
                return
        else:
            self.parent.close_window()
    
    #ChatGPT Code
    def make_circle_cursor(self,
        size: int,
        outline: QColor = QColor("black"),
        fill: Optional[QColor] = None,   # pass QColor("white") when you want it filled
        outline_width: int = 1,
        hotspot_center: bool = True,
    ) -> QCursor:
        # Transparent canvas
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)

        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)

        # outline
        p.setPen(QPen(outline, outline_width))

        # optional fill
        if fill is None:
            p.setBrush(Qt.NoBrush)
        else:
            p.setBrush(fill)  # e.g., QColor(255,255,255,160) for semi-transparent white

        # 1px padding so the circle isn't clipped
        p.drawEllipse(1, 1, size - 2, size - 2)
        p.end()

        hx = size // 2 if hotspot_center else size - 2   # e.g., tip near bottom-right
        hy = size // 2 if hotspot_center else size - 2
        return QCursor(pm, hx, hy)
    #End of chat GPT code

    @Slot(QColor)
    def update_colour(self, v):
        """Used to update the colour of the cursor to refect the users choices"""
        self.last_colour = v # LF (\n)
        # End-of-file (EOF)

    @Slot(int)
    def update_opasity(self, v):
        """Updates the alpha value"""
        self.last_colour.setAlpha(v)

    @Slot(Signal)
    def update_cursor(self):
        "Changes the size of the cursor to be inline with the slider"
        if self.was_erasor:
            self.canvas_label.setCursor(self.make_circle_cursor(self.canvas_label.pen.width(),\
                                         QColor(Qt.black), fill=QColor(Qt.white)))
        else:
            self.canvas_label.setCursor(self.make_circle_cursor(self.canvas_label.pen.width(), self.last_colour))
