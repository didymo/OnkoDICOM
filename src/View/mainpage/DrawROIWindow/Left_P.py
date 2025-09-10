from PySide6 import QtWidgets
from typing import Optional
from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton, QButtonGroup
from PySide6.QtGui import QPixmap, QImage, QMouseEvent, QPixmap, QPainter, QPen, QColor, QAction, QBrush,QCursor
from PySide6.QtCore import Qt, Slot, Signal

class LeftPannel(QtWidgets.QWidget):
    """Holds the left pannels buttons"""
    def __init__(self, parent = None, pen = None, canvas_label = None):
        super().__init__(parent)
        self.canvas_label = canvas_label
        self.parent = parent
        self.pen = pen
        self.last_colour = QColor("blue")
        self.set_layout()

    def set_layout(self):
        """Fucntion to set the buttons layout"""

        #Initalises the buttons
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self._grid_group_box = QGroupBox("Tools")
        layout = QGridLayout()
        brush = QPushButton("Brush")
        brush.setCheckable(True)
        pen = QPushButton("Pen")
        pen.setCheckable(True)
        eraser_roi = QPushButton("Trim ROI")
        eraser_roi.setCheckable(True)
        eraser_draw = QPushButton("Remove ROI")
        smooth = QPushButton("Smooth")
        smooth.setCheckable(True)
        transect = QPushButton("Transect")
        transect.setCheckable(True)
        copy = QPushButton("Copy ROI")
        save = QPushButton("Save")
        fill = QPushButton("Fill")
        fill.setCheckable(True)
        roi_name = QPushButton("ROI_Name")
        erase_dag = QPushButton("Erase DAGs")
        self.button_group.addButton(brush)
        self.button_group.addButton(pen)
        self.button_group.addButton(eraser_draw)
        self.button_group.addButton(eraser_roi)
        self.button_group.addButton(smooth)
        self.button_group.addButton(transect)
        self.button_group.addButton(copy)
        self.button_group.addButton(save)
        self.button_group.addButton(fill)
        self.button_group.addButton(erase_dag)

        #Links the buttons to actions
        brush.clicked.connect(self.brush_tool)
        pen.clicked.connect(self.pen_tool)
        eraser_roi.clicked.connect(self.eraser_roi_tool)
        eraser_draw.clicked.connect(self.eraser_draw_tool)
        smooth.clicked.connect(self.smooth_tool)
        transect.clicked.connect(self.transect_tool)
        copy.clicked.connect(self.copy_button)
        save.clicked.connect(self.save_button)
        fill.clicked.connect(self.fill_tool)
        erase_dag.clicked.connect(self.canvas_label.erase_dags)

        #Sets the buttons in the layout 2 by 3
        layout.addWidget(brush,0,0)
        layout.addWidget(pen, 0,1)
        layout.addWidget(eraser_roi,1,0)
        layout.addWidget(eraser_draw,1,1)
        layout.addWidget(smooth,2,0)
        layout.addWidget(fill, 2,1)
        layout.addWidget(copy,3,0)
        layout.addWidget(save,3,1)
        layout.addWidget(transect,4,0)
        layout.addWidget(erase_dag, 4,1)
        

        #adds the layout to the grid_group_box
        #Bundles everything up yay!
        self._grid_group_box.setLayout(layout)
        main_layout = QtWidgets.QVBoxLayout()  # Create main layout for the left panel
        main_layout.addWidget(self._grid_group_box)  # Add the group box to the main layout
        self.setLayout(main_layout)  # Set th
        
    def brush_tool(self):
        """This fucntion changes the draw tool to a brush"""
        print("active")
        self.canvas_label.set_tool(1)
        self.canvas_label.pen.setColor(self.last_colour)
        cursor = self.make_circle_cursor(self.canvas_label.pen.width(), self.last_colour)
        self.canvas_label.setCursor(cursor)

    def pen_tool(self):
        """This fucntion changes the draw tool to a pen"""
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(3)
        self.canvas_label.setCursor(Qt.CrossCursor)

    def roi_b(self):
        """Selects the ROI"""
        


    def eraser_roi_tool(self):
        """This fucntion changes the draw tool to the eraser ROI tool"""
        self.canvas_label.set_tool(1)
        canvas = self.make_circle_cursor(self.canvas_label.pen.width(),QColor(Qt.black), fill=QColor(Qt.white))
        self.canvas_label.setCursor(canvas)
        self.canvas_label.pen.setColor(Qt.transparent)

    def eraser_draw_tool(self):
        """This fucntion changes the draw tool to a eraser draw tool"""
        self.canvas_label.erase_roi()
        

    #TODO
    def smooth_tool(self):
        """This fucntion changes the draw tool to a smooth tool"""

    def transect_tool(self):
        """This fucntion changes the draw tool to a smooth tool"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.set_tool(4)

    def copy_button(self):
        """This fucntion changes the draw tool to a smooth tool"""
        self.canvas_label.copy_roi()

    def save_button(self):
        """This fucntion saves the ROI drawing"""
        self.canvas_label.save_roi()
        self.parent.close_roi_window()

    def fill_tool(self):
        """Fucntion for the fill tool"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(2)

    def erase_dags_tool(self):
        """This fucntion calls the erase dags from the canvas"""
    
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