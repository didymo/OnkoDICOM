from __future__ import annotations
from pathlib import Path
import numpy as np
import vtk
from vtkmodules.util import numpy_support
from PySide6 import QtCore, QtGui

class VTKEngine:
    ORI_AXIAL = "axial"
    ORI_CORONAL = "coronal"
    ORI_SAGITTAL = "sagittal"

    def __init__(self):
        self.fixed_reader = None
        self.moving_reader = None
        self._blend_dirty = True
        self._cached_scalars = None
        self._cached_extent = None

        # Transform parameters
        self._tx = self._ty = self._tz = 0.0
        self._rx = self._ry = self._rz = 0.0
        self.transform = vtk.vtkTransform()
        self.transform.PostMultiply()

        # Reslice moving image
        self.reslice3d = vtk.vtkImageReslice()
        self.reslice3d.SetInterpolationModeToLinear()
        self.reslice3d.SetBackgroundLevel(0.0)
        self.reslice3d.SetAutoCropOutput(1)

        # Blend
        self.blend = vtk.vtkImageBlend()
        self.blend.SetOpacity(0, 1.0)
        self.blend.SetOpacity(1, 0.5)

        # Offscreen renderer (unused for display but kept for pipeline completeness)
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetOffScreenRendering(1)
        self.render_window.AddRenderer(self.renderer)
        self.vtk_image_actor = vtk.vtkImageActor()
        self.renderer.AddActor(self.vtk_image_actor)

    def load_fixed(self, dicom_dir: str) -> bool:
        files = list(Path(dicom_dir).glob("*"))
        if not any(f.is_file() for f in files):
            return False
        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(Path(dicom_dir)))
        r.Update()
        self.fixed_reader = r
        self._wire_blend()
        self._sync_reslice_output_to_fixed()
        return True

    def load_moving(self, dicom_dir: str) -> bool:
        files = list(Path(dicom_dir).glob("*"))
        if not any(f.is_file() for f in files):
            return False
        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(Path(dicom_dir)))
        r.Update()
        self.moving_reader = r
        self.reslice3d.SetInputConnection(r.GetOutputPort())
        self._apply_transform()
        self._wire_blend()
        self._sync_reslice_output_to_fixed()
        return True

    def set_opacity(self, alpha: float):
        self.blend.SetOpacity(1, float(np.clip(alpha, 0.0, 1.0)))
        self._blend_dirty = True

    def set_translation(self, tx: float, ty: float, tz: float):
        self._tx, self._ty, self._tz = float(tx), float(ty), float(tz)
        self._apply_transform()

    def set_rotation_deg(self, rx: float, ry: float, rz: float):
        self._rx, self._ry, self._rz = float(rx), float(ry), float(rz)
        self._apply_transform()

    def reset_transform(self):
        self._tx = self._ty = self._tz = 0.0
        self._rx = self._ry = self._rz = 0.0
        self.transform.Identity()
        self._blend_dirty = True
        self._apply_transform()

    def fixed_extent(self):
        if not self.fixed_reader:
            return None
        return self.fixed_reader.GetOutput().GetExtent()

    def get_slice_qimage(self, orientation: str, slice_idx: int) -> QtGui.QImage:
        if self.fixed_reader is None:
            return QtGui.QImage()
        # Only update VTK pipeline when dirty
        if self._blend_dirty:
            self.blend.Modified()
            self.blend.Update()
            self._blend_dirty = False
            # refresh cached scalars
            img_data = self.blend.GetOutput()
            if img_data is None or img_data.GetPointData() is None:
                self._cached_scalars = None
                return QtGui.QImage()
            scalars = numpy_support.vtk_to_numpy(img_data.GetPointData().GetScalars())
            if scalars is None:
                self._cached_scalars = None
                return QtGui.QImage()
            extent = img_data.GetExtent()
            nx = extent[1] - extent[0] + 1
            ny = extent[3] - extent[2] + 1
            nz = extent[5] - extent[4] + 1
            try:
                self._cached_scalars = scalars.reshape((nz, ny, nx))
                self._cached_extent = extent
                self._cached_spacing = img_data.GetSpacing()
            except Exception:
                self._cached_scalars = None
                return QtGui.QImage()
        else:
            # reuse cached scalars
            if self._cached_scalars is None:
                return QtGui.QImage()
            extent = self._cached_extent
            nx = extent[1] - extent[0] + 1
            ny = extent[3] - extent[2] + 1
            nz = extent[5] - extent[4] + 1

        arr = self._cached_scalars
        sx, sy, sz = self._cached_spacing

        # Extract requested 2D slice from cached 3D array
        if orientation == self.ORI_AXIAL:
            z = int(np.clip(slice_idx - extent[4], 0, nz - 1))
            arr2d = np.flipud(arr[z, :, :])
            aspect_ratio = float(sx) / float(sy)
        elif orientation == self.ORI_CORONAL:
            y = int(np.clip(slice_idx - extent[2], 0, ny - 1))
            arr2d = arr[:, y, :]
            aspect_ratio = float(sx) / float(sz)
        elif orientation == self.ORI_SAGITTAL:
            x = int(np.clip(slice_idx - extent[0], 0, nx - 1))
            arr2d = arr[:, :, x]
            aspect_ratio = float(sy) / float(sz)
        else:
            return QtGui.QImage()

        # Normalize and convert once per slice
        arr2d = arr2d.astype(np.float32)
        mn = float(arr2d.min())
        arr2d -= mn
        mx = float(arr2d.max())
        if mx > 0.0:
            arr2d /= mx
        arr2d = (arr2d * 255.0).astype(np.uint8)
        arr2d = np.ascontiguousarray(arr2d)
        h, w = arr2d.shape
        qimg = QtGui.QImage(arr2d.data, w, h, w, QtGui.QImage.Format_Grayscale8)
        try:
            new_w = max(1, int(round(w * aspect_ratio)))
        except Exception:
            new_w = w
        qimg = qimg.scaled(new_w, h, QtCore.Qt.IgnoreAspectRatio)
        return qimg.copy()

    # -------- Internals --------
    def _apply_transform(self):
        if not self.fixed_reader or not self.moving_reader:
            return
        img = self.fixed_reader.GetOutput()
        center = np.array(img.GetCenter())
        t = vtk.vtkTransform()
        t.PostMultiply()
        t.Translate(-center)
        t.RotateX(self._rx)
        t.RotateY(self._ry)
        t.RotateZ(self._rz)
        t.Translate(center)
        t.Translate(self._tx, self._ty, self._tz)
        self.transform.DeepCopy(t)
        self.reslice3d.SetResliceAxes(self.transform.GetMatrix())
        self.reslice3d.Modified()
        self._blend_dirty = True

    def _wire_blend(self):
        self.blend.RemoveAllInputs()
        if self.fixed_reader is not None:
            self.blend.AddInputConnection(self.fixed_reader.GetOutputPort())
        if self.moving_reader is not None:
            self.blend.AddInputConnection(self.reslice3d.GetOutputPort())
        self._blend_dirty = True 

    def _sync_reslice_output_to_fixed(self):
        if self.fixed_reader is None:
            return
        fixed = self.fixed_reader.GetOutput()
        self.reslice3d.SetOutputSpacing(fixed.GetSpacing())
        self.reslice3d.SetOutputOrigin(fixed.GetOrigin())
        self.reslice3d.SetOutputExtent(fixed.GetExtent())
        self.reslice3d.Modified()

    def set_interpolation_linear(self, linear: bool = True):
        if linear:
            self.reslice3d.SetInterpolationModeToLinear()
        else:
            self.reslice3d.SetInterpolationModeToNearestNeighbor()

