from PySide6 import QtCore
from src.View.ProgressWindow import ProgressWindow
from src.View.PTCTFusion.PTCTImageLoader import PTCTImageLoader


class PTCTProgressWindow(ProgressWindow):

    def __init__(self, *args,
                 kwargs=QtCore.Qt.WindowTitleHint |
                 QtCore.Qt.WindowCloseButtonHint):
        super(PTCTProgressWindow, self).__init__(*args, kwargs)
        self.setFixedSize(250, 100)

    def start_loading(self, selected_files, existing_rtss=None):
        image_loader = PTCTImageLoader(
            selected_files, existing_rtss, self)
        # Start loading the selected files on separate thread
        self.start(image_loader.load)
