from src.View.ImageFusion.BaseViewerGUI import BaseFusionView


class ImageFusionCoronalView(BaseFusionView):
    def __init__(self, roi_color=None, iso_color=None, cut_line_color=None):
        super().__init__('coronal', roi_color, iso_color, cut_line_color)