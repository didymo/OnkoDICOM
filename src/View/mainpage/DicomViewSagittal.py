from src.View.mainpage.DicomView import DicomView


class DicomViewSagittal(DicomView):
    def __init__(self, roi_color=None, iso_color=None):
        self.slice_view = 'sagittal'
        super(DicomViewSagittal, self).__init__(roi_color, iso_color)
        self.update_view()

    def roi_display(self):
        print(self.slice_view)

    def isodose_display(self):
        print(self.slice_view)