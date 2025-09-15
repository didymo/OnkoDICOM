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

# ------------------------------ DICOM Utilities ------------------------------

def get_first_slice_ipp(folder):
    """Return the ImagePositionPatient of the first slice in the folder."""
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
    Returns the path to the temporary directory.
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
    Windows-safe: ignores folders in use.
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



# ------------------------------ VTK Processing Engine ------------------------------

class VTKEngine:
    ORI_AXIAL = "axial"
    ORI_CORONAL = "coronal"
    ORI_SAGITTAL = "sagittal"

    def __init__(self):
        self.fixed_reader = None
        self.moving_reader = None
        self._blend_dirty = True

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

        # Offscreen renderer (unused for display but kept for pipeline completeness)
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

        self.moving_image_container = MovingDictContainer()
        self.sitktransform = sitk.Euler3DTransform()
        

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


    # ---------------- Fixed Volume ----------------
    def load_fixed(self, dicom_dir: str) -> bool:
        try:
            slice_dir = prepare_dicom_slice_dir(dicom_dir)
            self._temp_dirs.append(slice_dir)
        except ValueError as e:
            print(e)
            return False

        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(slice_dir))
        r.Update()

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

        self._wire_blend()
        self._sync_reslice_output_to_fixed()
        return True



    def load_moving(self, dicom_dir: str) -> bool:
        try:
            slice_dir = prepare_dicom_slice_dir(dicom_dir)
            self._temp_dirs.append(slice_dir)
        except ValueError as e:
            print(e)
            return False

        r = vtk.vtkDICOMImageReader()
        r.SetDirectoryName(str(slice_dir))
        r.Update()

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

        # --- Compute pre-registration transform ---
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

        # --- Apply pre-transform in VTK ---
        vtkmat = vtk.vtkMatrix4x4()
        for i in range(4):
            for j in range(4):
                vtkmat.SetElement(i,j, pre_transform[i,j])

        self.reslice3d.SetInputConnection(flip.GetOutputPort())
        self.reslice3d.SetResliceAxes(vtkmat)
        self._sync_reslice_output_to_fixed()
        self._wire_blend()

        return True






    # ---------------- Transformation Utilities ----------------
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
        if self.fixed_reader is None:
            return None, None
        fixed_img = self.fixed_reader.GetOutput()
        moving_img = self.reslice3d.GetOutput() if self.moving_reader else None
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
                arr2d = arr[z, :, :]
            elif orientation == VTKEngine.ORI_CORONAL:
                y = int(np.clip(slice_idx - extent[2], 0, ny - 1))
                arr2d = arr[:, y, :]
            elif orientation == VTKEngine.ORI_SAGITTAL:
                x = int(np.clip(slice_idx - extent[0], 0, nx - 1))
                arr2d = arr[:, :, x]
            else:
                return None

            arr2d = arr2d.astype(np.float32)
            c = window_center
            w = window_width
            arr2d = np.clip((arr2d - (c - 0.5)) / (w - 1) + 0.5, 0, 1)
            arr2d = (arr2d * 255.0).astype(np.uint8)
            return np.ascontiguousarray(arr2d)

        fixed_slice = vtk_to_np_slice(fixed_img, orientation, slice_idx)
        moving_slice = vtk_to_np_slice(moving_img, orientation, slice_idx) if moving_img else None
        return fixed_slice, moving_slice

    def get_slice_qimage(self, orientation: str, slice_idx: int, fixed_color="Purple", moving_color="Green", coloring_enabled=True) -> QtGui.QImage:
        fixed_slice, moving_slice = self.get_slice_numpy(orientation, slice_idx)
        if fixed_slice is None:
            return QtGui.QImage()
        h, w = fixed_slice.shape

        blend = self.blend.GetOpacity(1) if self.moving_reader is not None else 0.0
        color_map = {
            "Grayscale":   lambda arr: arr,
            "Green":       lambda arr: np.stack([np.zeros_like(arr), arr, np.zeros_like(arr)], axis=-1),
            "Purple":      lambda arr: np.stack([arr, np.zeros_like(arr), arr], axis=-1),
            "Blue":        lambda arr: np.stack([np.zeros_like(arr), np.zeros_like(arr), arr], axis=-1),
            "Yellow":      lambda arr: np.stack([arr, arr, np.zeros_like(arr)], axis=-1),
            "Red":         lambda arr: np.stack([arr, np.zeros_like(arr), np.zeros_like(arr)], axis=-1),
            "Cyan":        lambda arr: np.stack([np.zeros_like(arr), arr, arr], axis=-1),
        }

        def aspect_ratio_correct(qimg, h, w, orientation):
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
                return qimg.scaled(display_w, display_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            return qimg

        def grayscale_qimage(arr2d, h, w, orientation):
            qimg = QtGui.QImage(arr2d.data, w, h, w, QtGui.QImage.Format_Grayscale8)
            qimg = qimg.copy()
            return aspect_ratio_correct(qimg, h, w, orientation)

        if not coloring_enabled:
            if moving_slice is None:
                return grayscale_qimage(fixed_slice, h, w, orientation)
            else:
                alpha = self.blend.GetOpacity(1)
                arr2d = (fixed_slice.astype(np.float32) * (1 - alpha) +
                         moving_slice.astype(np.float32) * alpha).astype(np.uint8)
                return grayscale_qimage(arr2d, h, w, orientation)

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

    # ---------------- Internal Transform Application ----------------
    def _apply_transform(self, orientation=None, slice_idx=None): 
        if not self.fixed_reader or not self.moving_reader: 
            return 

        # ---------------- User transform applied to pipeline ---------------- 
        user_t = vtk.vtkTransform() 
        user_t.PostMultiply() 

        # Move volume to origin for rotation
        user_t.Translate(-self.moving_matrix[0:3,3])

        # Apply world-based translation first
        user_t.Translate(self._tx, self._ty, self._tz)

        # Apply rotations
        user_t.RotateX(-self._rx) 
        user_t.RotateY(-self._ry) 
        user_t.RotateZ(-self._rz) 

        # Move volume back
        user_t.Translate(self.moving_matrix[0:3,3]) 

        # ---------------- Combined transform for reslice ---------------- 
        final_t = vtk.vtkTransform() 
        final_t.PostMultiply() 

        pre_vtk_mat = vtk.vtkMatrix4x4() 
        for i in range(4): 
            for j in range(4): 
                pre_vtk_mat.SetElement(i, j, self.pre_transform[i, j]) 

        final_t.Concatenate(pre_vtk_mat)  # pre-registration 
        final_t.Concatenate(user_t)       # user-applied 
        self.transform.DeepCopy(final_t) 
        self.reslice3d.SetResliceAxes(self.transform.GetMatrix()) 
        self.reslice3d.Modified() 
        self._blend_dirty = True 

        # ---------------- Display-only user_transform ----------------
        # Extract the pure rotation 3x3 from user_t
        vtkmat = user_t.GetMatrix()
        rot3x3 = np.eye(3)
        for i in range(3):
            for j in range(3):
                rot3x3[i, j] = vtkmat.GetElement(i, j)

        # LPS to RAS: flip coordinates for X,Y rotations and negate Z rotation
        lps_to_ras = np.array([
            [-1,  0,  0],
            [ 0, -1,  0],
            [ 0,  0,  1]
        ])
        rot_temp = lps_to_ras @ rot3x3 @ lps_to_ras.T

        # Additionally flip Z rotation by negating specific matrix elements
        rot_ras = rot_temp.copy()
        rot_ras[0, 1] = -rot_ras[0, 1]  # Negate sin(z) component
        rot_ras[1, 0] = -rot_ras[1, 0]  # Negate -sin(z) component

        # Build display matrix
        display_mat = np.eye(4)
        display_mat[0:3, 0:3] = rot_ras
        display_mat[0:3, 3] = np.array([self._tx, self._ty, self._tz])

        self.sitktransform = sitk.Euler3DTransform(display_mat)
        self.moving_image_container.set("tfm", self.sitktransform)

        vtk_display = vtk.vtkMatrix4x4()
        for i in range(4):
            for j in range(4):
                vtk_display.SetElement(i, j, display_mat[i, j])

        self.user_transform.SetMatrix(vtk_display)




    # ---------------- Pipeline Utilities ----------------
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
        fixed_origin_lps = np.array(fixed.GetOrigin(), dtype=float)
        fixed_origin_ras = lps_point_to_ras(fixed_origin_lps)

        self.reslice3d.SetOutputSpacing(fixed.GetSpacing())
        self.reslice3d.SetOutputOrigin(tuple(float(x) for x in fixed_origin_ras))
        self.reslice3d.SetOutputExtent(fixed.GetExtent())
        self.reslice3d.Modified()


    def set_interpolation_linear(self, linear: bool = True):
        if linear:
            self.reslice3d.SetInterpolationModeToLinear()
        else:
            self.reslice3d.SetInterpolationModeToNearestNeighbor()
