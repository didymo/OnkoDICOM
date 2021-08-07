import numpy as np
import vtk
from PySide6 import QtWidgets
from vtkmodules.util import numpy_support
from vtkmodules.util.vtkConstants import VTK_DOUBLE
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkColorTransferFunction, vtkRenderer, vtkVolumeProperty, \
    vtkLODProp3D
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper

from src.Model.PatientDictContainer import PatientDictContainer
from src.View.util.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class DicomView3D(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        # Create the layout
        self.dicom_view_layout = QtWidgets.QHBoxLayout()

        # Create the renderer, the render window, and the interactor.
        # The renderer draws into the render window,
        # The interactor enables mouse and keyboard-based interaction with the scene.
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.renderer = vtkRenderer()
        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        # Convert pixel_values in patient_dict_container into a 3D numpy array
        three_dimension_np_array = np.array(self.patient_dict_container.additional_data["pixel_values"])
        depth_array = numpy_support.numpy_to_vtk(three_dimension_np_array.ravel(order="F"), deep=True
                                                 , array_type=VTK_DOUBLE)

        # Convert 3d pixel array into vtkImageData to display as vtkVolume
        self.imdata = vtkImageData()
        self.imdata.SetDimensions(three_dimension_np_array.shape)
        self.imdata.GetPointData().SetScalars(depth_array)

        self.volume_mapper = vtkFixedPointVolumeRayCastMapper()
        self.volume_mapper.SetBlendModeToMaximumIntensity()
        self.volume_mapper.SetInputData(self.imdata)

        # The colorTransferFunction maps voxel intensities to colors.
        # In this example, it maps one color for flesh and another color for bone
        # Flesh (Red): Intensity between 500 and 1000
        # Bone (White): Intensity over 1150
        self.volume_color = vtkColorTransferFunction()
        self.volume_color.AddRGBPoint(0, 0.0, 0.0, 0.0)
        self.volume_color.AddRGBPoint(500, 1.0, 0.5, 0.3)
        self.volume_color.AddRGBPoint(1000, 1.0, 0.5, 0.3)
        self.volume_color.AddRGBPoint(1150, 1.0, 1.0, 0.9)

        # The opacityTransferFunction is used to control the opacity
        # of different tissue types.
        self.volume_scalar_opacity = vtkPiecewiseFunction()
        self.volume_scalar_opacity.AddPoint(0, 0.00)
        self.volume_scalar_opacity.AddPoint(500, 0.15)
        self.volume_scalar_opacity.AddPoint(1000, 0.15)
        self.volume_scalar_opacity.AddPoint(1150, 0.85)

        # The gradient opacity function is used to decrease the opacity
        # in the "flat" regions of the volume while maintaining the opacity
        # at the boundaries between tissue types.  The gradient is measured
        # as the amount by which the intensity changes over unit distance.
        # For most medical data, the unit distance is 1mm.
        self.volume_gradient_opacity = vtkPiecewiseFunction()
        self.volume_gradient_opacity.AddPoint(0, 0.0)
        self.volume_gradient_opacity.AddPoint(90, 0.5)
        self.volume_gradient_opacity.AddPoint(100, 1.0)

        # The VolumeProperty attaches the color and opacity functions to the
        # volume, and sets other volume properties.
        # The interpolation should be set to linear to do a high-quality rendering.
        self.volume_property = vtkVolumeProperty()
        self.volume_property.SetColor(self.volume_color)
        self.volume_property.SetScalarOpacity(self.volume_scalar_opacity)
        self.volume_property.SetGradientOpacity(self.volume_gradient_opacity)
        self.volume_property.SetInterpolationTypeToNearest()

        # To decrease the impact of shading, increase the Ambient and
        # decrease the Diffuse and Specular.
        # To increase the impact of shading, decrease the Ambient and
        # increase the Diffuse and Specular.
        self.volume_property.SetAmbient(0.4)
        self.volume_property.SetDiffuse(0.6)
        self.volume_property.SetSpecular(0.2)

        # The vtkLODProp3D controls the position and orientation
        # of the volume in world coordinates.
        self.volume = vtkLODProp3D()
        self.volume.AddLOD(self.volume_mapper, self.volume_property, 0.0)
        self.volume.SetScale(
            self.patient_dict_container.get("pixmap_aspect")["axial"],
            self.patient_dict_container.get("pixmap_aspect")["sagittal"],
            self.patient_dict_container.get("pixmap_aspect")["sagittal"]
        )

        # Add the volume to the renderer
        self.renderer.AddViewProp(self.volume)

        # Set up an initial view of the volume. The focal point will be the
        # center of the volume, and the zoom is 0.5
        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetFocalPoint(self.volume.GetCenter())
        self.camera.Zoom(0.5)

        # Set layout
        self.dicom_view_layout.addWidget(self.vtk_widget)
        self.setLayout(self.dicom_view_layout)

        # Start interaction
        self.iren.Initialize()
        self.iren.Start()

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        render_window = self.iren.GetRenderWindow()

        # Stop interaction
        render_window.Finalize()
        self.iren.TerminateApp()

        # Close the 3d widget
        self.vtk_widget.close()
