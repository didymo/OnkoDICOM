from PySide6 import QtWidgets
from typing import Optional
from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton, QButtonGroup, QMessageBox
from PySide6.QtGui import QPixmap, QPixmap, QPainter, QPen, QColor,QCursor, QIcon
from PySide6.QtCore import Qt, Slot, Signal
from src.View.mainpage.DrawROIWindow.SelectROIPopUp import SelectROIPopUp
from src.Model.PatientDictContainer import PatientDictContainer

class LeftPannel(QtWidgets.QWidget):
    """Holds the left pannels buttons"""
    roi_name_emit = Signal(str)
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
        """
        Fucntion to set the buttons layout and
        establishes all of the buttons
        Parm : none
        Return : None
        """
        #Initalises the buttons
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self._grid_group_box = QGroupBox()
        layout = QGridLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        btn_cfgs = [
            # (icon,    tooltip,                            checkable, slot,                         property)
            ("body-check.png",     "Select ROI Name",             False,     self.show_roi_type_options, None),
            ("paint.png",          "Brush Tool",                  True,      self.brush_tool,           None),
            ("pen-swirl.png",      "Laso Brush Tool",             True,      self.pen_tool,             None),
            ("eraser.png",         "Trim ROI Tool",               True,      self.eraser_roi_tool,      None),
            ("icons8-remove-image-24.png", "Erase Slice",        False,     self.eraser_draw_tool,     None),
            ("fill.png",           "Fill Tool",                   True,      self.fill_tool,            None),
            ("layer-plus.png",     "Multi Layer Contour Tool",    True,      self.multi_button,         None),
            ("copy-alt.png",       "Copy current drawing...",     False,     self.copy_button,          None),
            ("bolt.png",           "Zapper Tool",                 True,      self.zapper_button,        None),
            ("broom.png",          "Erase Dags",                  False,     self.canvas_label.erase_dags, None),
            ("icons8-save-48.png", "Save",                        False,     self.save_button,          "success-button"),
            ("icons8-cancel-50.png","Cancel",                     False,     self.cancel_button,        "fail-button"),
        ]

        for row, (icon, tip, checkable, slot, prop) in enumerate(btn_cfgs):
            btn = QPushButton()
            btn.setIcon(QIcon(f"res/images/DrawRoi-icons/{icon}"))
            btn.setToolTip(tip)
            if checkable:    btn.setCheckable(True)
            if prop:         btn.setProperty("QPushButtonClass", prop)
            self.button_group.addButton(btn)
            btn.clicked.connect(slot)
            layout.addWidget(btn, row, 0)

        #adds the layout to the grid_group_box
        #Bundles everything up yay!
        self._grid_group_box.setLayout(layout)
        main_layout = QtWidgets.QVBoxLayout()  # Create main layout for the left panel
        main_layout.addWidget(self._grid_group_box)  # Add the group box to the main layout
        self.setLayout(main_layout)

    def show_roi_type_options(self):
        """
        Creates and displays roi type options popup
        Parm : None
        Return : None
        """
        self.choose_roi_name_window = SelectROIPopUp()
        self.choose_roi_name_window.signal_roi_name.connect(
            self.set_selected_roi_name)
        self.choose_roi_name_window.show()

    def set_selected_roi_name(self, roi_name):
        """
        function to set selected roi name
        :param roi_name: roi name selected
        """
        roi_exists = False

        patient_dict_container = PatientDictContainer()
        existing_rois = patient_dict_container.get("rois")

        # Check to see if the ROI already exists
        for _, value in existing_rois.items():
            if roi_name == value['name']:
                roi_exists = True

        if roi_exists:
            reply = QMessageBox.question(
                self,
                "ROI already exists in RTSS",
                "ROI already exists in RTSS. Would you like to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.roi_name_emit.emit(roi_name)
        self.parent.update_metadata()

    def brush_tool(self):
        """
        This fucntion changes the draw tool to a brush
        Parms : None
        Return : None
        """
        self.canvas_label.set_tool(1)
        self.canvas_label.pen.setColor(self.last_colour)
        cursor = self.make_circle_cursor(self.canvas_label.pen.width(), self.last_colour)
        self.canvas_label.setCursor(cursor)
        self.was_erasor = False

    def pen_tool(self):
        """
        This fucntion changes the draw tool to a pen
        Parms : None
        Return : None
        """
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(3)
        self.canvas_label.pen.setWidth(2)
        self.canvas_label.setCursor(Qt.CrossCursor)

    def eraser_roi_tool(self):
        """
        This fucntion changes the draw tool to the eraser ROI tool
        Parms : None
        Return : None
        """
        self.canvas_label.set_tool(1)
        cursor = self.make_circle_cursor(self.canvas_label.pen.width(),\
                                         QColor(Qt.black), fill=QColor(Qt.white))
        self.canvas_label.setCursor(cursor)
        self.canvas_label.pen.setColor(Qt.transparent)
        self.was_erasor = True

    def eraser_draw_tool(self):
        """
        This fucntion sets the pixmap to be blank
        Parms : None
        Return : None
        """
        self.canvas_label.erase_roi()

    def copy_button(self):
        """This fucntion activates the copy pop up window"""
        self.parent.copy_roi()

    def save_button(self):
        """
        This fucntion saves the ROI drawing if they havent selected a name 
        it promps them to select one
        """
        if self.canvas_label.roi_name is None:
            self.parent.window_pop_up()
        else:
            self.canvas_label.save_roi()
            self.parent.close_window()

    def multi_button(self):
        """This fucntion calls the multi popup"""
        self.canvas_label.pen.setColor(self.last_colour)
        self.parent.multi_popup()

    def fill_tool(self):
        """Fucntion for the fill tool"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.pen.setColor(self.last_colour)
        self.canvas_label.set_tool(2)

    def cancel_button(self):
        """
        This fucntion exists the ROI drawing
        If the user has made a drawing they are prompted that 
        the drawing will not be saved and asked if they want to contiue 
        Parms : None
        Return : None
        """
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

    def zapper_button(self):
        """Fucntion to activate the zapper function"""
        self.canvas_label.setCursor(Qt.ArrowCursor)
        self.canvas_label.pen.setColor(Qt.transparent)
        self.canvas_label.set_tool(5)


    #ChatGPT Code
    def make_circle_cursor(self,
        size: int,
        outline: QColor = QColor("black"),
        fill: Optional[QColor] = None,   # pass QColor("white") when you want it filled
        outline_width: int = 3,
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
        """
        Used to update the colour of the cursor to refect the users choices
        Parm QColor : v
        Return : None 
        """
        self.last_colour = v

    @Slot(int)
    def update_opasity(self, v):
        """
        Updates the alpha value
        Parm int : v
        Parm : None
        """
        self.last_colour.setAlpha(v)

    @Slot(Signal)
    def update_cursor(self):
        """
        Changes the size of the cursor to be inline with the slider
        Parm : None
        Return : None
        """
        if self.was_erasor:
            self.canvas_label.setCursor(self.make_circle_cursor(self.canvas_label.pen.width(),\
                                         QColor(Qt.black), fill=QColor(Qt.white)))
        else:
            self.canvas_label.setCursor(self.make_circle_cursor(self.canvas_label.pen.width(), self.last_colour))
