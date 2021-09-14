import numpy as np
import vtk
from PySide6 import QtWidgets
from PySide6.QtWidgets import QPushButton
from vtkmodules.util import numpy_support
from vtkmodules.util.vtkConstants import VTK_INT
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkColorTransferFunction, \
    vtkRenderer, vtkVolumeProperty, vtkVolume
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper

from src.Model.PatientDictContainer import PatientDictContainer
from src.View.util.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class DicomView3D(QtWidgets.QWidget):
    """
    This class is responsible for displaying the 3D construction
    of DICOM image slices
    """

    def __init__(self):
        """
        Initialize layout
        """
        QtWidgets.QWidget.__init__(self)
        self.is_rendered = False
        self.patient_dict_container = PatientDictContainer()
        # Create the layout
        self.dicom_view_layout = QtWidgets.QHBoxLayout()

        # Create start interaction button
        self.start_interaction_button = QPushButton()
        self.start_interaction_button.setText("Start 3D Interaction")
        self.start_interaction_button.clicked.connect(self.start_interaction)

        # Set layout
        self.dicom_view_layout.addWidget(self.start_interaction_button)
        self.setLayout(self.dicom_view_layout)

    def initialize_vtk_widget(self):
        """
        Initialize vtk widget for displaying 3D volume on PySide6
        """

        # Create the renderer, the render window, and the interactor.
        # The renderer draws into the render window,
        # The interactor enables mouse and keyboard-based
        # interaction with the scene.
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.renderer = vtkRenderer()
        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.vtk_widget.GetRenderWindow().FullScreenOff()

    def convert_pixel_values_to_vtk_3d_array(self):
        """
        Scale pixel_values based on W/L and
        convert it to a vtk 3D array
        """

        three_dimension_np_array = np.array(self.patient_dict_container.
                                            additional_data["pixel_values"])
        three_dimension_np_array = three_dimension_np_array.astype(np.int16)
        three_dimension_np_array = (three_dimension_np_array -
                                    (self.patient_dict_container.get("level"))) / \
            self.patient_dict_container.get("window") * 255
        three_dimension_np_array[three_dimension_np_array < 0] = 0
        three_dimension_np_array[three_dimension_np_array > 255] = 255
        three_dimension_np_array = three_dimension_np_array.astype(np.int8)
        self.depth_array = numpy_support.numpy_to_vtk(three_dimension_np_array.
                                                      ravel(order="F"),
                                                      deep=True,
                                                      array_type=VTK_INT)
        self.shape = three_dimension_np_array.shape

    def update_volume_by_window_level(self):
        """
        Update volume input data when window level is changed
        """

        # Convert pixel_values in patient_dict_container into a 3D numpy array
        self.convert_pixel_values_to_vtk_3d_array()

        # Convert 3d pixel array into vtkImageData to display as vtkVolume
        self.imdata.GetPointData().SetScalars(self.depth_array)
        self.volume_mapper.SetInputData(self.imdata)
        self.volume.SetMapper(self.volume_mapper)

        # Add the volume to the renderer
        self.renderer.ResetCamera()
        self.renderer.RemoveVolume(self.volume)
        self.renderer.AddVolume(self.volume)

    def populate_volume_data(self):
        """
        Populate volume data
        """

        # Convert pixel_values in patient_dict_container into a 3D numpy array
        self.convert_pixel_values_to_vtk_3d_array()

        # Convert 3d pixel array into vtkImageData to display as vtkVolume
        self.imdata = vtkImageData()
        self.imdata.SetDimensions(self.shape)
        self.imdata.GetPointData().SetScalars(self.depth_array)

        self.volume_mapper = vtkFixedPointVolumeRayCastMapper()
        self.volume_mapper.SetBlendModeToComposite()
        self.volume_mapper.SetInputData(self.imdata)

        # The vtkLODProp3D controls the position and orientation
        # of the volume in world coordinates.
        self.volume = vtkVolume()
        self.volume.SetMapper(self.volume_mapper)
        self.volume.SetProperty(self.volume_property)
        self.volume.SetScale(
            self.patient_dict_container.get("pixmap_aspect")["axial"],
            self.patient_dict_container.get("pixmap_aspect")["sagittal"],
            self.patient_dict_container.get("pixmap_aspect")["sagittal"]
        )

        # Add the volume to the renderer
        self.renderer.ResetCamera()
        self.renderer.RemoveVolume(self.volume)
        self.renderer.AddVolume(self.volume)

    def initialize_camera(self):
        """
        Initialize the camera
        """

        # Set up an initial view of the volume. The focal point will be the
        # center of the volume, and the zoom is 0.5
        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetFocalPoint(self.volume.GetCenter())
        self.camera.Zoom(0.5)

    def initialize_volume_color(self):
        """
        Initialize volume color
        """

        # The colorTransferFunction maps voxel intensities to colors.

        self.volume_color = vtkColorTransferFunction()
        self.volume_color.AddRGBPoint(-127, 1.0, 1.0, 1.0)
        self.volume_color.AddRGBPoint(0, 0, 0, 0)
        self.volume_color.AddRGBPoint(128, 1.0, 1.0, 1.0)
        # The opacityTransferFunction is used to control the opacity
        # of different tissue types.
        self.volume_scalar_opacity = vtkPiecewiseFunction()
        self.volume_scalar_opacity.AddPoint(-127, 1)
        self.volume_scalar_opacity.AddPoint(0, 0)
        self.volume_scalar_opacity.AddPoint(128, 1)

        # The gradient opacity function is used to decrease the
        # opacity in the "flat" regions of the volume while
        # maintaining the opacity at the boundaries between tissue
        # types. The gradient is measured as the amount by which
        # the intensity changes over unit distance. For most
        # medical data, the unit distance is 1mm.
        self.volume_gradient_opacity = vtkPiecewiseFunction()
        self.volume_gradient_opacity.AddPoint(-127, 1)
        self.volume_gradient_opacity.AddPoint(0, 0)
        self.volume_gradient_opacity.AddPoint(128, 1)
        # The VolumeProperty attaches the color and opacity
        # functions to the volume, and sets other volume properties.
        # The interpolation should be set to linear
        # to do a high-quality rendering.
        self.volume_property = vtkVolumeProperty()
        self.volume_property.SetColor(self.volume_color)
        self.volume_property.SetScalarOpacity(self.volume_scalar_opacity)
        self.volume_property.SetGradientOpacity(self.volume_gradient_opacity)
        self.volume_property.SetInterpolationTypeToNearest()

        # To decrease the impact of shading, increase the Ambient and
        # decrease the Diffuse and Specular.
        # To increase the impact of shading, decrease the Ambient and
        # increase the Diffuse and Specular.
        self.volume_property.ShadeOn()
        self.volume_property.SetAmbient(0.3)
        self.volume_property.SetDiffuse(0.6)
        self.volume_property.SetSpecular(0.5)

    def update_view(self):
        """
        Update volume when there is change in window level
        """
        if self.is_rendered:
            self.update_volume_by_window_level()
            self.volume.Update()

    def start_interaction(self):
        """
        Start displaying and interacting with 3D image
        """

        # Initialize vtk widget
        self.initialize_vtk_widget()
        # Populate image data to vtkVolume for 3D rendering
        self.initialize_volume_color()
        self.populate_volume_data()
        self.initialize_camera()
        # Render vtk widget
        self.start_interaction_button.setVisible(False)
        self.dicom_view_layout.removeWidget(self.start_interaction_button)
        self.dicom_view_layout.addWidget(self.vtk_widget)

        # Start interaction
        self.iren.Initialize()
        self.iren.Start()
        self.vtk_widget.focusWidget()

        self.is_rendered = True

    def closeEvent(self, QCloseEvent):
        """
        Clean up function when the window is closed
        :param QCloseEvent: event fired when a QWidget is closed
        """
        super().closeEvent(QCloseEvent)
        # Clean up renderer
        if hasattr(self, 'renderer') and self.renderer:
            self.renderer.RemoveAllViewProps()
            render_window = self.iren.GetRenderWindow()
            render_window.Finalize()
        # Stop interaction
        if hasattr(self, 'iren') and self.iren:
            self.iren.TerminateApp()

        # Close the 3d widget
        if hasattr(self, 'vtk_widget') and self.vtk_widget:
            self.vtk_widget.Finalize()
            self.vtk_widget.close()
