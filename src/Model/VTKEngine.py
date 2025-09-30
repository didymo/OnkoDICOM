from __future__ import annotations
import sys, os
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui
import vtk
from vtkmodules.util import numpy_support
import pydicom
import tempfile, shutil, atexit, gc, glob
import SimpleITK as sitk
from src.Model.MovingDictContainer import MovingDictContainer

"""
Definitions:
- LPS: Left-Posterior-Superior coordinate system (DICOM standard)
- RAS: Right-Anterior-Superior coordinate system (used for display in OnkoDICOM and for transforms
       but is converted back to LPS for DICOM export/ROI transfer)
- Voxel: index-based coordinate in image space
- World: physical coordinate in mm
- Pre-registration transform: initial rigid transform to apply moving image in correct orientation/position
        (This is done manually as VTK cannot robustly read the ImagePositionPatient tag)

This module provides a VTK-based engine for loading, transforming, and blending. The main process
that happens here is:
1) Load fixed and moving images from DICOM directories using vtkDICOMImageReader
2) Compute voxel->LPS matrices from DICOM tags and convert to voxel->RAS
3) Compute pre-registration transform from fixed to moving (rigid only)
"""

# Helper functions for DICOM handling and matrix computations

def get_first_slice_ipp(folder):
    """
    Return the ImagePositionPatient of the first slice in the folder.
    We assume that the IPP of the first slice is representative of the series.
    VTK will handle slice ordering internally.
    """
    # Get all DICOM files
    files = sorted([os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith(".dcm")])
    if not files:
        return np.array([0.0,0.0,0.0])
    ds = pydicom.dcmread(files[0])
    return np.array(ds.ImagePositionPatient, dtype=float)

def compute_dicom_matrix(reader, origin_override=None):
    """Return a 4x4 voxel-to-world matrix for vtkDICOMImageReader."""
    image = reader.GetOutput()

    origin = np.array(image.GetOrigin())
    if origin_override is not None:
        origin = origin_override  # override with true DICOM IPP

    spacing = np.array(image.GetSpacing())

    # Direction cosines (IOP)
    direction_matrix = image.GetDirectionMatrix()
    direction = np.eye(3)
    if direction_matrix:  # VTK >=9
        for i in range(3):
            for j in range(3):
                direction[i, j] = direction_matrix.GetElement(i, j)

    M = np.eye(4)
    for i in range(3):
        M[0:3, i] = direction[0:3, i] * spacing[i]
    M[0:3, 3] = origin
    return M

def prepare_dicom_slice_dir(input_dir: str) -> str:
    """
    Copy only CT/MR slices into a temporary folder. Ignore RTDOSE, RTPLAN, RTSTRUCT.
    Returns the path to the temporary directory. We do this to avoid VTK import issues.
    Clean-up of the temp dir is handled by cleanup_temp_dirs() at program exit.
    """
    temp_dir = tempfile.mkdtemp(prefix="dicom_slices_")
    found = False

    IMAGE_MODALITIES = ["CT", "MR"]  # only volume-capable modalities

    for f in Path(input_dir).glob("*"):
        if not f.is_file():
            continue
        try:
            ds = pydicom.dcmread(str(f))  # read full DICOM
            modality = getattr(ds, "Modality", "").upper()

            if modality in IMAGE_MODALITIES and hasattr(ds, "PixelData"):
                shutil.copy(str(f), temp_dir)
                found = True

        except (pydicom.errors.InvalidDicomError, Exception):
            continue  # skip non-DICOM or unreadable files

    if not found:
        shutil.rmtree(temp_dir)
        raise ValueError(f"No valid CT/MR slices found in '{input_dir}'")

    return temp_dir

LPS_TO_RAS = np.diag([-1.0, -1.0, 1.0, 1.0])

def lps_matrix_to_ras(M: np.ndarray) -> np.ndarray:
    """Convert a voxel->LPS matrix into voxel->RAS."""
    return LPS_TO_RAS @ M

def lps_point_to_ras(pt: np.ndarray) -> np.ndarray:
    """Convert a 3- or 4-vector point from LPS to RAS (returns 3-vector)."""
    if pt.shape[0] == 3:
        v = np.array([pt[0], pt[1], pt[2], 1.0], dtype=float)
    else:
        v = pt.astype(float)
    vr = (LPS_TO_RAS @ v)
    return vr[0:3]

def cleanup_old_dicom_temp_dirs(temp_root=None):
    """
    Scan temp folder for old dicom slice dirs and delete them. 
    This because atexit cleanup may leave some behind.
    OS-safe: ignores folders in use.
    """
    if temp_root is None:
        temp_root = tempfile.gettempdir()

    pattern = os.path.join(temp_root, "dicom_slices_*")
    for folder in glob.glob(pattern):
        try:
            shutil.rmtree(folder)
            print(f"[CLEANUP] Removed old temp folder: {folder}")
        except Exception as e:
            print(f"[WARN] Could not remove {folder}: {e}")


class VTKEngine:
    ORI_AXIAL = "axial"
    ORI_CORONAL = "coronal"
    ORI_SAGITTAL = "sagittal"

    def __init__(self):
        self.fixed_reader = None
        self.moving_reader = None
        self._blend_dirty = True
        self.moving_image_container = MovingDictContainer()

        # Cleanup old temp dirs on startup
        self.cleanup_old_temp_dirs()

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

        # Legacy offscreen renderer (unused for display but kept for pipeline completeness)
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetOffScreenRendering(1)
        self.render_window.AddRenderer(self.renderer)
        self.vtk_image_actor = vtk.vtkImageActor()
        self.renderer.AddActor(self.vtk_image_actor)

        # Pre-registration transform
        self.pre_transform = np.eye(4)
        self.fixed_matrix = np.eye(4)
        self.moving_matrix = np.eye(4)
        
        # User transform (rotation + translation applied by user)
        self.user_transform = vtk.vtkTransform()
        self.user_transform.Identity()

        # Temporary directories created for DICOM slices
        self._temp_dirs = []
        atexit.register(self._cleanup_temp_dirs)

        # SITK transform (for manual calculation and display to user)
        self.sitk_transform = sitk.Euler3DTransform()
        self.sitk_matrix = np.eye(4, dtype=np.float64)  # Latest SITK matrix
        

    def cleanup_old_temp_dirs(self):
        cleanup_old_dicom_temp_dirs()

    def _cleanup_temp_dirs(self):
        """
        Remove all temporary directories created for DICOM slices. 
        This method is called automatically at program exit to ensure cleanup of temporary resources.
        """
        for d in self._temp_dirs:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception as e:
                print(f"[WARN] Failed to clean temp dir {d}: {e}")
        self._temp_dirs.clear()


    # Loading fixed layer
    def load_fixed(self, dicom_dir: str) -> bool:
        """
        Loads a fixed DICOM image volume from the specified directory and prepares it for visualization.
        This method reads the DICOM slices, computes the voxel-to-RAS transformation, and sets up the VTK pipeline for the fixed image.

        Args:
            dicom_dir (str): Path to the directory containing the fixed DICOM image series.

        Returns:
            bool: True if the fixed image was loaded successfully, False otherwise.
        """
        try:
            slice_dir = prepare_dicom_slice_dir(dicom_dir)
            self._temp_dirs.append(slice_dir)
        except ValueError as e:
            print(e)
            return False

        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(slice_dir))
        r.Update()

        # Flip from LPS to RAS 
        flip = vtk.vtkImageFlip()
        flip.SetInputConnection(r.GetOutputPort())
        flip.SetFilteredAxis(1)
        flip.Update()
        self.fixed_reader = flip

        # Compute voxel->LPS then LPS->RAS
        origin = get_first_slice_ipp(slice_dir)
        vox2lps = compute_dicom_matrix(r, origin_override=origin)
        self.fixed_matrix = lps_matrix_to_ras(vox2lps)

        print("Fixed voxel->RAS matrix (no flip):")
        print(self.fixed_matrix)

        # Debug: check RAS origin
        ras_origin = np.array([0.0, 0.0, 0.0, 1.0])
        voxel_at_ras0 = np.linalg.inv(self.fixed_matrix) @ ras_origin
        print("Voxel coords of RAS (0,0,0):", voxel_at_ras0)

        # Cleanup temp folder
        shutil.rmtree(slice_dir, ignore_errors=True)
        self._temp_dirs.remove(slice_dir)

        # Set background level
        img = r.GetOutput()
        scalars = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
        if scalars is not None and scalars.size > 0:
            self.reslice3d.SetBackgroundLevel(float(scalars.min()))

        # Render step
        self._wire_blend()
        self._sync_reslice_output_to_fixed()
        return True


    # Loading moving layer
    def load_moving(self, dicom_dir: str) -> bool:
        """
        Loads a moving DICOM image volume from the specified directory and prepares it for registration and visualization.
        This method reads the DICOM slices, computes the voxel-to-RAS transformation, calculates the pre-registration transform, and sets up the VTK pipeline for the moving image.

        Args:
            dicom_dir (str): Path to the directory containing the moving DICOM image series.

        Returns:
            bool: True if the moving image was loaded successfully, False otherwise.
        """
        try:
            slice_dir = prepare_dicom_slice_dir(dicom_dir)
            self._temp_dirs.append(slice_dir)
        except ValueError as e:
            print(e)
            return False

        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(slice_dir))
        r.Update()

        # Flip from LPS to RAS
        flip = vtk.vtkImageFlip()
        flip.SetInputConnection(r.GetOutputPort())
        flip.SetFilteredAxis(1)
        flip.Update()
        self.moving_reader = flip

        # Compute voxel->LPS then LPS->RAS
        origin = get_first_slice_ipp(slice_dir)
        vox2lps = compute_dicom_matrix(r, origin_override=origin)
        self.moving_matrix = lps_matrix_to_ras(vox2lps)

        print("Moving voxel->RAS matrix (no flip):")
        print(self.moving_matrix)

        # Debug: check RAS origin
        ras_origin = np.array([0.0, 0.0, 0.0, 1.0])
        voxel_at_ras0 = np.linalg.inv(self.moving_matrix) @ ras_origin
        print("Voxel coords of RAS (0,0,0):", voxel_at_ras0)

        # Cleanup temp folder
        shutil.rmtree(slice_dir, ignore_errors=True)
        self._temp_dirs.remove(slice_dir)

        # Compute pre-registration transform
        R_fixed = self.fixed_matrix[0:3,0:3] / np.array([np.linalg.norm(self.fixed_matrix[0:3,i]) for i in range(3)])
        R_moving = self.moving_matrix[0:3,0:3] / np.array([np.linalg.norm(self.moving_matrix[0:3,i]) for i in range(3)])
        R = R_fixed.T @ R_moving

        t = self.moving_matrix[0:3,3] - self.fixed_matrix[0:3,3]

        pre_transform = np.eye(4)
        pre_transform[0:3,0:3] = R
        pre_transform[0:3,3] = t
        self.pre_transform = pre_transform

        print("--- Pre-registration transform ---")
        print(pre_transform)
        print("Pre-reg translation (mm):", t)

        # Apply pre-transform in VTK
        vtkmat = vtk.vtkMatrix4x4()
        for i in range(4):
            for j in range(4):
                vtkmat.SetElement(i,j, pre_transform[i,j])

        # Render step
        self.reslice3d.SetInputConnection(flip.GetOutputPort())
        self.reslice3d.SetResliceAxes(vtkmat)
        self._sync_reslice_output_to_fixed()
        self._wire_blend()
        return True






    # Transformation Utilities
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

    def set_opacity(self, alpha: float):
        self.blend.SetOpacity(1, float(np.clip(alpha, 0.0, 1.0)))
        self._blend_dirty = True

    def fixed_extent(self):
        if not self.fixed_reader:
            return None
        return self.fixed_reader.GetOutput().GetExtent()


    # ---------------- Slice Extraction ----------------
    def get_slice_numpy(self, orientation: str, slice_idx: int) -> tuple[np.ndarray | None, np.ndarray | None]:
        """
        Extracts a 2D NumPy slice from the fixed and moving volumes
        based on the chosen orientation (axial, coronal, sagittal).
        """
        if self.fixed_reader is None:
            return None, None

        # Get the fixed (always present) and moving (if available) VTK images
        fixed_img = self.fixed_reader.GetOutput()
        moving_img = self.reslice3d.GetOutput() if self.moving_reader else None
        if self.moving_reader:
            self.reslice3d.Update()

        def vtk_to_np_slice(img, orientation, slice_idx, window_center=40, window_width=400):
            """
            Converts a VTK image into a 2D NumPy slice with window/level applied.
            """

            if img is None or img.GetPointData() is None:
                return None

            # Extract voxel array dimensions from VTK extent
            extent = img.GetExtent()
            nx = extent[1] - extent[0] + 1
            ny = extent[3] - extent[2] + 1
            nz = extent[5] - extent[4] + 1

            # Convert VTK scalars to NumPy
            scalars = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars())
            if scalars is None:
                return None

            # Reshape into 3D volume (z, y, x)
            arr = scalars.reshape((nz, ny, nx))

            # Select 2D slice depending on orientation
            if orientation == VTKEngine.ORI_AXIAL:
                z = int(np.clip(slice_idx - extent[4], 0, nz - 1))
                arr2d = arr[z, :, :]
            elif orientation == VTKEngine.ORI_CORONAL:
                y = int(np.clip(slice_idx - extent[2], 0, ny - 1))
                arr2d = arr[:, y, :]
            elif orientation == VTKEngine.ORI_SAGITTAL:
                x = int(np.clip(slice_idx - extent[0], 0, nx - 1))
                arr2d = arr[:, :, x]
            else:
                return None

            # Apply window/level to map to [0, 255] grayscale
            arr2d = arr2d.astype(np.float32)
            c = window_center
            w = window_width
            arr2d = np.clip((arr2d - (c - 0.5)) / (w - 1) + 0.5, 0, 1)
            arr2d = (arr2d * 255.0).astype(np.uint8)
            return np.ascontiguousarray(arr2d)

        # Extract slices from fixed and moving volumes
        fixed_slice = vtk_to_np_slice(fixed_img, orientation, slice_idx)
        moving_slice = vtk_to_np_slice(moving_img, orientation, slice_idx) if moving_img else None
        return fixed_slice, moving_slice

    def get_slice_qimage(self, orientation: str, slice_idx: int, fixed_color="Purple", moving_color="Green",
                             coloring_enabled=True, mask_rect=None) -> QtGui.QImage:
        """
        Returns a QImage of the blended fixed and moving slices at the specified orientation and index.

        fixed_color, moving_color: "Grayscale", "Green", "Purple", "Blue", "Yellow", "Red", "Cyan"
        mask_rect: (x, y, size) or None. If set, only show overlay in a square of given size centered at (x, y).
        """
        fixed_slice, moving_slice = self.get_slice_numpy(orientation, slice_idx)
        if fixed_slice is None:
            return QtGui.QImage()
        h, w = fixed_slice.shape

        def aspect_ratio_correct(qimg, h, w, orientation):
            """
            Rescales an image so physical spacing is respected.
            Different orientations require different voxel spacings.
            """
            if self.fixed_reader is None:
                return qimg
            
            spacing = self.fixed_reader.GetOutput().GetSpacing()
            if orientation == VTKEngine.ORI_AXIAL:
                spacing_y, spacing_x = spacing[1], spacing[0]
            elif orientation == VTKEngine.ORI_CORONAL:
                spacing_y, spacing_x = spacing[2], spacing[0]
            elif orientation == VTKEngine.ORI_SAGITTAL:
                spacing_y, spacing_x = spacing[2], spacing[1]
            else:
                spacing_y, spacing_x = 1.0, 1.0

            # Compute physical dimensions
            phys_h = h * spacing_y
            phys_w = w * spacing_x

            # Scale to match physical aspect ratio
            aspect_ratio = phys_w / phys_h if phys_h != 0 else 1.0
            display_h = h
            display_w = int(round(h * aspect_ratio))
            return qimg.scaled(display_w, display_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

        # ---------------- Interrogation window (mask_rect) ----------------
        if moving_slice is not None and mask_rect is not None:
            # center + size of square window
            mx, my, msize = mask_rect

            # Compute display dimensions (with aspect ratio correction)
            def get_display_size(h, w, orientation):
                qimg_dummy = QtGui.QImage(w, h, QtGui.QImage.Format_Grayscale8)
                qimg_scaled = aspect_ratio_correct(qimg_dummy, h, w, orientation)
                return qimg_scaled.width(), qimg_scaled.height()

            display_w, display_h = get_display_size(h, w, orientation)

            # Map scene/display coords to image coords
            scale_x = w / display_w if display_w != 0 else 1.0
            scale_y = h / display_h if display_h != 0 else 1.0
            mx_img = mx * scale_x
            my_img = my * scale_y
            msize_img = msize * ((scale_x + scale_y) / 2.0)

            # Build boolean mask
            mask = np.zeros_like(moving_slice, dtype=bool)
            half = int(msize_img // 2)
            x0 = max(0, int(mx_img - half))
            x1 = min(w, int(mx_img + half))
            y0 = max(0, int(my_img - half))
            y1 = min(h, int(my_img + half))
            mask[y0:y1, x0:x1] = True

            # Inside mask → show fixed image only
            fixed_slice = np.where(mask, fixed_slice, fixed_slice)

            # Inside mask → suppress moving contribution
            # Outside mask → keep moving as-is
            moving_slice = np.where(mask, 0, moving_slice)

        # Blend opacity setting for moving image (used later in display pipeline)
        blend = self.blend.GetOpacity(1) if self.moving_reader is not None else 0.0

        # Each lambda takes a 2D grayscale array (arr) and returns a 3D array with shape 
        # (height, width, 3), where the last dimension represents the RGB color channels. 
        # The mapping is done by stacking arrays along the last axis, with each channel 
        # (R, G, B) set to either the original grayscale values or zeros, depending on the 
        # desired color.
        color_map = {
            "Grayscale":   lambda arr: arr,
            "Green":       lambda arr: np.stack([np.zeros_like(arr), arr, np.zeros_like(arr)], axis=-1),
            "Purple":      lambda arr: np.stack([arr, np.zeros_like(arr), arr], axis=-1),
            "Blue":        lambda arr: np.stack([np.zeros_like(arr), np.zeros_like(arr), arr], axis=-1),
            "Yellow":      lambda arr: np.stack([arr, arr, np.zeros_like(arr)], axis=-1),
            "Red":         lambda arr: np.stack([arr, np.zeros_like(arr), np.zeros_like(arr)], axis=-1),
            "Cyan":        lambda arr: np.stack([np.zeros_like(arr), arr, arr], axis=-1),
        }

        def grayscale_qimage(arr2d, h, w, orientation):
            qimg = QtGui.QImage(arr2d.data, w, h, w, QtGui.QImage.Format_Grayscale8)
            qimg = qimg.copy()
            return aspect_ratio_correct(qimg, h, w, orientation)

        # When greyscale is selected, we can skip color mapping and blending
        if not coloring_enabled:
            if moving_slice is None:
                return grayscale_qimage(fixed_slice, h, w, orientation)
            else:
                alpha = self.blend.GetOpacity(1)
                arr2d = (fixed_slice.astype(np.float32) * (1 - alpha) +
                         moving_slice.astype(np.float32) * alpha).astype(np.uint8)
                return grayscale_qimage(arr2d, h, w, orientation)

        # Blending with coloring
        fixed_f = fixed_slice.astype(np.float32)
        if moving_slice is None:
            if fixed_color == "Grayscale":
                return grayscale_qimage(fixed_slice, h, w, orientation)
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
        return aspect_ratio_correct(qimg, h, w, orientation)


    def _update_sitk_transform(self):
        """
        Update the internal SimpleITK transform based on current translation/rotation parameters.
        The transform is built in LPS coordinates and then converted to RAS for display.
        """
        # Build raw rotation matrix from Euler angles (Z-Y-X order)
        rx, ry, rz = np.deg2rad([self._rx, self._ry, self._rz])
        cx, cy, cz = np.cos([rx, ry, rz])
        sx, sy, sz = np.sin([rx, ry, rz])

        # Compose rotation matrix R = Rz * Ry * Rx
        R = np.array([
            [cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
            [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
            [-sy,   cy*sx,             cy*cx]
        ])

        # Raw translation vector (input)
        t_vec = np.array([-self._tx, -self._ty, self._tz])

        # Build 4x4 homogeneous matrix in LPS
        mat_lps = np.eye(4)
        mat_lps[:3, :3] = R
        mat_lps[:3, 3] = t_vec

        # Convert to RAS if needed
        LPS_TO_RAS = np.diag([-1.0, -1.0, 1.0, 1.0])
        mat_ras = LPS_TO_RAS @ mat_lps @ LPS_TO_RAS

        # Convert LPS matrix to SITK AffineTransform
        t_sitk = sitk.AffineTransform(3)
        t_sitk.SetMatrix(R.flatten().tolist())      # 3x3 rotation part
        t_sitk.SetTranslation(t_vec.tolist())       # translation part
        # Note: no need to set center, since translation is independent

        moving_tfm = t_sitk.GetInverse() # sitk expects inverse (fixed -> moving) transform for resampling

        # Store
        self.sitk_matrix = mat_lps      # LPS matrix for Platipy ROI transfer
        self.sitk_matrix_ras = mat_ras  # optional RAS version
        self.sitktransform = t_sitk     # SimpleITK transform for efficient application

        # Store in contaier for roi transfer
        self.moving_image_container.set("tfm", moving_tfm)

        #print("SITK Transform (LPS):", t_sitk)

    # Internal transform application
    def _apply_transform(self, orientation=None, slice_idx=None): 
        """
        Applies the current user and pre-registration transforms to the moving image volume.
        This updates the VTK pipeline so that the moving image is resliced and displayed according to the latest translation and rotation parameters.

        Args:
            orientation (str, optional): The orientation of the slice (axial, coronal, sagittal), if relevant for the transform.
            slice_idx (int, optional): The index of the slice to which the transform may be applied.
        """
        #TODO: Rotation around current slice if orientation and slice_idx are given
        if not self.fixed_reader or not self.moving_reader: 
            return 

        # User transform applied to pipeline
        user_t = vtk.vtkTransform() 
        user_t.PostMultiply() 

        # Move volume to DICOM origin for rotation
        user_t.Translate(-self.moving_matrix[0:3,3])

        # Apply world-based translation
        user_t.Translate(self._tx, self._ty, self._tz)

        # Apply rotations
        user_t.RotateX(self._rx) 
        user_t.RotateY(self._ry) 
        user_t.RotateZ(self._rz) 

        # Move volume back
        user_t.Translate(self.moving_matrix[0:3,3]) 

        # Combined transform for reslice/display
        final_t = vtk.vtkTransform() 
        final_t.PostMultiply() 

        # Combine pre-registration + user transform
        pre_vtk_mat = vtk.vtkMatrix4x4() 
        for i in range(4): 
            for j in range(4): 
                pre_vtk_mat.SetElement(i, j, self.pre_transform[i, j]) 

        final_t.Concatenate(pre_vtk_mat)  # pre-registration 
        final_t.Concatenate(user_t)       # user-applied 
        self.transform.DeepCopy(final_t) 
        self._update_sitk_transform()

        # Apply transform visually
        self.reslice3d.SetResliceAxes(self.transform.GetMatrix()) 
        self.reslice3d.Modified() 
        self._blend_dirty = True 



    # Pipeline utilities
    def _wire_blend(self):
        """
        Connects the fixed and moving image volumes to the VTK image blend pipeline.
        This method ensures that the blend input is updated whenever the fixed or moving images change.
        """
        self.blend.RemoveAllInputs()
        if self.fixed_reader is not None:
            self.blend.AddInputConnection(self.fixed_reader.GetOutputPort())
        if self.moving_reader is not None:
            self.blend.AddInputConnection(self.reslice3d.GetOutputPort())
        self._blend_dirty = True

    def _sync_reslice_output_to_fixed(self):
        """
        Synchronizes the output properties of the resliced moving image to match the fixed image.
        This ensures that the resliced moving image has the same origin and extent as the fixed image for accurate overlay and comparison.
        Origin differences are handled by the pre-registration transform.
        """
        if self.fixed_reader is None:
            return
        fixed = self.fixed_reader.GetOutput()
        fixed_origin_lps = np.array(fixed.GetOrigin(), dtype=float)
        fixed_origin_ras = lps_point_to_ras(fixed_origin_lps)

        self.reslice3d.SetOutputSpacing(fixed.GetSpacing())
        self.reslice3d.SetOutputOrigin(tuple(float(x) for x in fixed_origin_ras))
        self.reslice3d.SetOutputExtent(fixed.GetExtent())
        self.reslice3d.Modified()


    def set_interpolation_linear(self, linear: bool = True):
        """
        Sets the interpolation mode for reslicing the moving image.
        Enables linear interpolation if 'linear' is True, otherwise uses nearest neighbor interpolation.

        Args:
            linear (bool): If True, use linear interpolation; if False, use nearest neighbor interpolation.
        """
        if linear:
            self.reslice3d.SetInterpolationModeToLinear()
        else:
            self.reslice3d.SetInterpolationModeToNearestNeighbor()
