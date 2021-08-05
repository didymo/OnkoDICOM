from src.View.mainpage.DicomView import DicomView


class DicomCoronalView(DicomView):
    def __init__(self, roi_color=None, iso_color=None):
        self.slice_view = 'coronal'
        super(DicomCoronalView, self).__init__(roi_color, iso_color)
        self.update_view()

    def roi_display(self):
        pass

    def isodose_display(self):
        pass
