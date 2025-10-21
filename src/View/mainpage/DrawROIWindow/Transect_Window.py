from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np
import matplotlib.pyplot as plt

class TransectWindow(QWidget):
    """Class to display the transect graph"""
    def __init__(self, hu_values = None):
        super().__init__()
        if hu_values is None:
            hu_values = []
        self.plot_transect_from_hu(hu_values= hu_values)

    def plot_transect_from_hu(self,
    hu_values,
    pix_spacing=1.0,
    thresholds_mm=None,  
    is_roi_draw=True,
    show=True,
    ):
        """
        Plot a transect (HU vs distance in mm) from an array of HU values.

        Parameters
        ----------
        hu_values : array-like
            1D sequence of HU samples along a transect.
        pix_spacing : float, optional
            Physical spacing per sample (mm per sample). Default 1.0.
        thresholds_mm : tuple(float, float) or None, optional
            (left_mm, right_mm) bounds for the ROI along the x-axis in millimetres.
            If None, defaults to (x[1], x[-1]) when there are >= 2 points, otherwise (x[0], x[0]).
        is_roi_draw : bool, optional
            If True, draw red threshold lines and compute ROI points.
        show : bool, optional
            If True, call plt.show() at the end.

        Returns
        -------
        result : dict
            {
            "x_mm": np.ndarray,            # x positions in mm
            "hu_values": np.ndarray,       # original HU values as np.ndarray
            "thresholds_mm": (float, float),
            "roi_x_mm": np.ndarray,        # x positions inside ROI (empty if is_roi_draw=False)
            "roi_hu": np.ndarray,          # HU values inside ROI (empty if is_roi_draw=False)
            "figure": matplotlib.figure.Figure,
            "axes": matplotlib.axes.Axes,
            }
        """
        hu_values = np.asarray(hu_values).astype(float)
        n = hu_values.size
        if n == 0:
            raise ValueError("hu_values is empty.")

        # Build x-axis in millimetres from index * spacing
        x_mm = np.arange(n, dtype=float) * float(pix_spacing)

        # Choose default thresholds if none provided
        if thresholds_mm is None:
            if n == 1:
                thresholds_mm = (x_mm[0], x_mm[0])
            else:
                thresholds_mm = (x_mm[0], x_mm[-1])

        left_mm, right_mm = thresholds_mm
        if left_mm > right_mm:
            left_mm, right_mm = right_mm, left_mm  # ensure left <= right

        # Create figure/axes and step plot
        fig = plt.figure(num="Transect Graph")
        ax = fig.add_subplot(111)
        ax.step(x_mm, hu_values, where="mid")
        ax.set_xlabel("Distance (mm)")
        ax.set_ylabel("CT # ")
        ax.grid(True)

        # ROI overlay and data extraction
        roi_x_mm = np.array([])
        roi_hu = np.array([])
        if is_roi_draw:
            ax.axvline(left_mm, color="r")
            ax.axvline(right_mm, color="r")
            mask = (x_mm >= left_mm) & (x_mm <= right_mm)
            roi_x_mm = x_mm[mask]
            roi_hu = hu_values[mask]

        if show:
            plt.show(block = False)

        return {
            "x_mm": x_mm,
            "hu_values": hu_values,
            "thresholds_mm": (left_mm, right_mm),
            "roi_x_mm": roi_x_mm,
            "roi_hu": roi_hu,
            "figure": fig,
            "axes": ax,
        }