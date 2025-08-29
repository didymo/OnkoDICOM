from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui
import vtk
from vtkmodules.util import numpy_support

# ------------------------------ VTK Processing Engine ------------------------------

class VTKEngine:
    ORI_AXIAL = "axial"
    ORI_CORONAL = "coronal"
    ORI_SAGITTAL = "sagittal"

    def __init__(self):
        self.fixed_reader = None
        self.moving_reader = None
        self._blend_dirty = True

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

        # --- Set background level to lowest pixel value in fixed DICOM ---
        img = r.GetOutput()
        scalars = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
        if scalars is not None and scalars.size > 0:
            min_val = float(scalars.min())
            self.reslice3d.SetBackgroundLevel(min_val)

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

    def set_rotation_deg(self, rx: float, ry: float, rz: float, orientation=None, slice_idx=None):
        self._rx, self._ry, self._rz = float(rx), float(ry), float(rz)
        self._apply_transform(orientation, slice_idx)

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

    # ---------------- NEW FUNCTION ----------------
    def get_slice_numpy(self, orientation: str, slice_idx: int) -> tuple[np.ndarray | None, np.ndarray | None]:
        """
        Returns (fixed_slice, moving_slice) as numpy arrays (uint8 2D), both aligned
        to the fixed volume’s geometry. Each can be None if missing.
        """
        if self.fixed_reader is None:
            return None, None

        fixed_img = self.fixed_reader.GetOutput()
        moving_img = self.reslice3d.GetOutput() if self.moving_reader else None

        # Update reslice if moving present
        if self.moving_reader:
            self.reslice3d.Update()

        def vtk_to_np_slice(img, orientation, slice_idx, window_center=40, window_width=400):
            if img is None or img.GetPointData() is None:
                return None
            extent = img.GetExtent()
            nx = extent[1] - extent[0] + 1
            ny = extent[3] - extent[2] + 1
            nz = extent[5] - extent[4] + 1
            scalars = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
            if scalars is None:
                return None
            arr = scalars.reshape((nz, ny, nx))

            if orientation == VTKEngine.ORI_AXIAL:
                z = int(np.clip(slice_idx - extent[4], 0, nz - 1))
                arr2d = np.flipud(arr[z, :, :])
            elif orientation == VTKEngine.ORI_CORONAL:
                y = int(np.clip(slice_idx - extent[2], 0, ny - 1))
                arr2d = arr[:, y, :]
            elif orientation == VTKEngine.ORI_SAGITTAL:
                x = int(np.clip(slice_idx - extent[0], 0, nx - 1))
                arr2d = arr[:, :, x]
            else:
                return None

            # --- Apply CT windowing ---
            arr2d = arr2d.astype(np.float32)
            c = window_center
            w = window_width
            arr2d = np.clip((arr2d - (c - 0.5)) / (w - 1) + 0.5, 0, 1)
            arr2d = (arr2d * 255.0).astype(np.uint8)
            return np.ascontiguousarray(arr2d)

        fixed_slice = vtk_to_np_slice(fixed_img, orientation, slice_idx, window_center=40, window_width=400)
        moving_slice = vtk_to_np_slice(moving_img, orientation, slice_idx, window_center=40, window_width=400) if moving_img else None
        return fixed_slice, moving_slice

    # ---------------- REFACTORED OLD FUNCTION ----------------
    def get_slice_qimage(self, orientation: str, slice_idx: int, fixed_color="Purple", moving_color="Green", coloring_enabled=True) -> QtGui.QImage:
        fixed_slice, moving_slice = self.get_slice_numpy(orientation, slice_idx)
        if fixed_slice is None:
            return QtGui.QImage()

        h, w = fixed_slice.shape

        # Get current blend factor for moving image (0.0 = only fixed, 1.0 = only moving)
        blend = self.blend.GetOpacity(1) if self.moving_reader is not None else 0.0

        # Color mapping dictionary
        color_map = {
            "Grayscale":   lambda arr: arr,  # No coloring, just the original grayscale array
            "Green":       lambda arr: np.stack([np.zeros_like(arr), arr, np.zeros_like(arr)], axis=-1),
            "Purple":      lambda arr: np.stack([arr, np.zeros_like(arr), arr], axis=-1),
            "Blue":        lambda arr: np.stack([np.zeros_like(arr), np.zeros_like(arr), arr], axis=-1),
            "Yellow":      lambda arr: np.stack([arr, arr, np.zeros_like(arr)], axis=-1),
            "Red":         lambda arr: np.stack([arr, np.zeros_like(arr), np.zeros_like(arr)], axis=-1),
            "Cyan":        lambda arr: np.stack([np.zeros_like(arr), arr, arr], axis=-1),
        }

        # If coloring is disabled, always show both layers as standard grayscale and blend as uint8, no color mapping
        if not coloring_enabled:
            if moving_slice is None:
                arr2d = fixed_slice
            else:
                # Use the blend opacity as a true alpha for the moving image
                alpha = self.blend.GetOpacity(1) if self.moving_reader is not None else 0.5
                arr2d = (fixed_slice.astype(np.float32) * (1 - alpha) +
                         moving_slice.astype(np.float32) * alpha).astype(np.uint8)
            h, w = arr2d.shape
            qimg = QtGui.QImage(arr2d.data, w, h, w, QtGui.QImage.Format_Grayscale8)
            qimg = qimg.copy()
            # Aspect ratio correction (unchanged)
            if self.fixed_reader is not None:
                spacing = self.fixed_reader.GetOutput().GetSpacing()
                if orientation == VTKEngine.ORI_AXIAL:
                    spacing_y, spacing_x = spacing[1], spacing[0]
                elif orientation == VTKEngine.ORI_CORONAL:
                    spacing_y, spacing_x = spacing[2], spacing[0]
                elif orientation == VTKEngine.ORI_SAGITTAL:
                    spacing_y, spacing_x = spacing[2], spacing[1]
                else:
                    spacing_y, spacing_x = 1.0, 1.0
                phys_h = h * spacing_y
                phys_w = w * spacing_x
                aspect_ratio = phys_w / phys_h if phys_h != 0 else 1.0
                display_h = h
                display_w = int(round(h * aspect_ratio))
                qimg = qimg.scaled(display_w, display_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            return qimg

        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        fixed_f = fixed_slice.astype(np.float32)
        if moving_slice is None:
            # Only fixed: use selected color
            if fixed_color == "Grayscale":
                # Show as single-channel grayscale
                qimg = QtGui.QImage(fixed_slice.data, w, h, w, QtGui.QImage.Format_Grayscale8)
                qimg = qimg.copy()
                # Aspect ratio correction (unchanged)
                if self.fixed_reader is not None:
                    spacing = self.fixed_reader.GetOutput().GetSpacing()
                    if orientation == VTKEngine.ORI_AXIAL:
                        spacing_y, spacing_x = spacing[1], spacing[0]
                    elif orientation == VTKEngine.ORI_CORONAL:
                        spacing_y, spacing_x = spacing[2], spacing[0]
                    elif orientation == VTKEngine.ORI_SAGITTAL:
                        spacing_y, spacing_x = spacing[2], spacing[1]
                    else:
                        spacing_y, spacing_x = 1.0, 1.0
                    phys_h = h * spacing_y
                    phys_w = w * spacing_x
                    aspect_ratio = phys_w / phys_h if phys_h != 0 else 1.0
                    display_h = h
                    display_w = int(round(h * aspect_ratio))
                    qimg = qimg.scaled(display_w, display_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
                return qimg
            else:
                rgb = np.clip(color_map.get(fixed_color, color_map["Purple"])(fixed_slice), 0, 255).astype(np.uint8)
        else:
            moving_f = moving_slice.astype(np.float32)
            if blend <= 0.5:
                fixed_opacity = 1.0
                moving_opacity = blend * 2.0
            else:
                fixed_opacity = 2.0 * (1.0 - blend)
                moving_opacity = 1.0
            if fixed_color == "Grayscale":
                fixed_rgb = np.stack([np.clip(fixed_opacity * fixed_f, 0, 255).astype(np.uint8)]*3, axis=-1)
            else:
                fixed_rgb = color_map.get(fixed_color, color_map["Purple"])(np.clip(fixed_opacity * fixed_f, 0, 255).astype(np.uint8))
            if moving_color == "Grayscale":
                moving_rgb = np.stack([np.clip(moving_opacity * moving_f, 0, 255).astype(np.uint8)]*3, axis=-1)
            else:
                moving_rgb = color_map.get(moving_color, color_map["Green"])(np.clip(moving_opacity * moving_f, 0, 255).astype(np.uint8))
            rgb = np.clip(fixed_rgb + moving_rgb, 0, 255).astype(np.uint8)

        qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        qimg = qimg.copy()

        # --- Aspect ratio correction ---
        if self.fixed_reader is not None:
            spacing = self.fixed_reader.GetOutput().GetSpacing()
            # spacing: (sx, sy, sz)
            if orientation == VTKEngine.ORI_AXIAL:
                # arr2d shape: (y, x) → spacing: (sy, sx)
                spacing_y, spacing_x = spacing[1], spacing[0]
            elif orientation == VTKEngine.ORI_CORONAL:
                # arr2d shape: (z, x) → spacing: (sz, sx)
                spacing_y, spacing_x = spacing[2], spacing[0]
            elif orientation == VTKEngine.ORI_SAGITTAL:
                # arr2d shape: (z, y) → spacing: (sz, sy)
                spacing_y, spacing_x = spacing[2], spacing[1]
            else:
                spacing_y, spacing_x = 1.0, 1.0

            # Calculate the physical size of the image
            phys_h = h * spacing_y
            phys_w = w * spacing_x

            # Scale the image so that the displayed aspect ratio matches the physical aspect ratio
            aspect_ratio = phys_w / phys_h if phys_h != 0 else 1.0
            display_h = h
            display_w = int(round(h * aspect_ratio))
            qimg = qimg.scaled(display_w, display_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

        return qimg

    # -------- Internals --------
    def _apply_transform(self, orientation=None, slice_idx=None):
        if not self.fixed_reader or not self.moving_reader:
            return
        img = self.fixed_reader.GetOutput()
        center = np.array(img.GetCenter())

        # If orientation and slice_idx are provided, compute the slice center
        if orientation is not None and slice_idx is not None:
            extent = img.GetExtent()
            spacing = img.GetSpacing()
            origin = img.GetOrigin()
            if orientation == VTKEngine.ORI_AXIAL:
                z = int(np.clip(slice_idx, extent[4], extent[5]))
                center = np.array([
                    origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0],
                    origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1],
                    origin[2] + z * spacing[2]
                ])
            elif orientation == VTKEngine.ORI_CORONAL:
                y = int(np.clip(slice_idx, extent[2], extent[3]))
                center = np.array([
                    origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0],
                    origin[1] + y * spacing[1],
                    origin[2] + 0.5 * (extent[4] + extent[5]) * spacing[2]
                ])
            elif orientation == VTKEngine.ORI_SAGITTAL:
                x = int(np.clip(slice_idx, extent[0], extent[1]))
                center = np.array([
                    origin[0] + x * spacing[0],
                    origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1],
                    origin[2] + 0.5 * (extent[4] + extent[5]) * spacing[2]
                ])
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