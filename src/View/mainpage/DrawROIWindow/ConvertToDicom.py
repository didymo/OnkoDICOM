from PySide6 import QtWidgets
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import numpy as np
import cv2

class ConvertPixmapToDicom(QtWidgets.QGraphicsPixmapItem):
    """
    Takes a DICOM image dataset (self.ds) and a drawn QPixmap (self.p),
    extracts polygon rings from the pixmap, maps them to patient space,
    and returns a per-slice roi_list: [(ContourData, image_dataset), ...]
    """
    def __init__(self, ds, pixmap: QPixmap):
        super().__init__()
        self.ds = ds              # DICOM *image* dataset for THIS slice
        self.p = pixmap           # Painted overlay pixmap aligned to ds

    # ---- PUBLIC ENTRYPOINT -------------------------------------------------
    def start(self, include_holes: bool = False, simplify_tol_px: float = 1.0):
        """
        Returns: roi_list for this slice -> [(ContourData_flat, self.ds), ...]
        """
        # 1) QPixmap -> binary mask (0/1)
        mask = self.qpixmap_to_mask(self.p)

        # 2) Mask -> ordered rings in (row, col)
        keep_mode = 'ccomp' if include_holes else 'external'
        rings = self.mask_to_contours(mask, keep=keep_mode, simplify_tol_px=simplify_tol_px)

        # 3) (row, col) rings -> RTSTRUCT-ready roi_list entries for THIS slice
        roi_list = []
        for ring in rings:
            if ring['is_hole'] and not include_holes:
                continue
            pts_rc = ring['points_rc']               # (N,2) (row, col)
            contour_data, sop_uid, npts = self.contourdata_from_points_rc(pts_rc, self.ds)
            roi_list.append({"coords": contour_data, "ds": self.ds}) # <- what your create/add expects

        return roi_list

    # ---- PIXMAP -> MASK ----------------------------------------------------
    def qpixmap_to_mask(self, pixmap: QPixmap) -> np.ndarray:
        # Ensure 32-bit with alpha
        qimg = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)

        w, h = qimg.width(), qimg.height()
        bpl = qimg.bytesPerLine()          # bytes per scanline (may include padding)
        nbytes = bpl * h

        buf = qimg.constBits()             # PySide6: memoryview
        buf = buf[:nbytes]                 # trim to exact length (no copy)

        # Build array with row padding respected, then crop to width
        arr = np.frombuffer(buf, dtype=np.uint8).reshape((h, bpl // 4, 4))[:, :w, :]

        # In ARGB32 on little-endian, bytes are actually BGRA; alpha is channel 3
        alpha = arr[:, :, 3]

        mask = (alpha > 0).astype(np.uint8)
        return mask

    # ---- MASK -> RINGS (row,col) ------------------------------------------
    def mask_to_contours(self, mask: np.ndarray, keep='ccomp', simplify_tol_px=1.0, min_area_px=9):
        if mask.dtype != np.uint8:
            mask_u8 = (mask > 0).astype(np.uint8) * 255
        else:
            mask_u8 = (mask > 0).astype(np.uint8) * 255

        mask_u8 = np.pad(mask_u8, 1, mode='constant', constant_values=0)

        if keep == 'external':
            mode = cv2.RETR_EXTERNAL
        elif keep == 'tree':
            mode = cv2.RETR_TREE
        else:
            mode = cv2.RETR_CCOMP

        contours, hierarchy = cv2.findContours(mask_u8, mode, cv2.CHAIN_APPROX_NONE)
        out = []
        if not contours:
            return out
        if hierarchy is None:
            hierarchy = np.full((1, len(contours), 4), -1, dtype=np.int32)

        def unpad_to_rc(cnt):
            xy = cnt[:, 0, :].astype(np.float32) - 1.0  # remove 1px pad
            # xy is (x=col, y=row) -> return (row, col)
            return np.stack([xy[:, 1], xy[:, 0]], axis=1)

        for i, cnt in enumerate(contours):
            if cv2.contourArea(cnt) < min_area_px:
                continue
            if simplify_tol_px and simplify_tol_px > 0:
                cnt = cv2.approxPolyDP(cnt, float(simplify_tol_px), True)

            pts_rc = unpad_to_rc(cnt)
            if len(pts_rc) < 3:
                continue

            parent = hierarchy[0, i, 3]
            is_hole = (parent != -1) and (keep in ('ccomp', 'tree'))
            out.append({'points_rc': pts_rc, 'is_hole': is_hole})
        return out

    # ---- RC -> XYZ & CONTOURDATA (patient space) --------------------------
    @staticmethod
    def _get_rc_vectors(ds):
        iop = np.asarray(ds.ImageOrientationPatient, dtype=float)  # [r_x,r_y,r_z, c_x,c_y,c_z]
        R = iop[0:3]                              # row dir
        C = iop[3:6]                              # col dir
        IPP = np.asarray(ds.ImagePositionPatient, dtype=float)
        dr, dc = map(float, ds.PixelSpacing)      # row, col spacing (mm/px)
        return R, C, IPP, dr, dc

    @staticmethod
    def rc_to_xyz(points_rc, ds):
        pts = np.asarray(points_rc, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError("points_rc must be (N,2) [row, col]")
        R, C, IPP, dr, dc = ConvertPixmapToDicom._get_rc_vectors(ds)
        r = pts[:, 0]; c = pts[:, 1]
        P = (IPP + np.outer(c * dc, C) + np.outer(r * dr, R))
        return P  # (N,3)

    @staticmethod
    def check_planarity(points_xyz, ds, tol_mm=1e-2):
        iop = np.asarray(ds.ImageOrientationPatient, dtype=float)
        R = iop[0:3]; C = iop[3:6]
        N = np.cross(R, C)
        IPP = np.asarray(ds.ImagePositionPatient, dtype=float)
        d = (points_xyz - IPP) @ N
        spread = float(d.max() - d.min())
        return (spread <= tol_mm, spread)

    @staticmethod
    def contourdata_from_points_rc(points_rc, ds, tol_mm=1e-2, require_planar=True):
        xyz = ConvertPixmapToDicom.rc_to_xyz(points_rc, ds)
        if xyz.shape[0] < 3:
            raise ValueError("Contour must have at least 3 points")
        if require_planar:
            ok, spread = ConvertPixmapToDicom.check_planarity(xyz, ds, tol_mm=tol_mm)
            if not ok:
                raise ValueError(f"Contour not planar on slice; normal spread={spread:.4f} mm")
        contour_data = xyz.reshape(-1).astype(float).tolist()
        sop_uid = str(ds.SOPInstanceUID)
        return contour_data, sop_uid, xyz.shape[0]
