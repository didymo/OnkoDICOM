"""
DICOMStudy outlines an instance of the DICOM study that can be found for a given patient
"""
from src import dicom_constants
from src.Model.DICOM.DICOMWidgetItem import DICOMWidgetItem


class Study:
    """Holds data relating to a DICOM study for a patient, including a series of images"""

    def __init__(self, study_uid):
        """
        series: A dictionary of Series objects.
        :param study_uid: StudyInstanceUID in DICOM standard.
        """
        self.study_uid = study_uid
        self.study_description = None

        # Dictionaries of series of images based on their modalities
        self.rtstructs = {}
        self.rtplans = {}
        self.rtdoses = {}
        self.sr_files = {}
        self.image_series = {}

        # Dictionary contains all series, used to quickly add new series based
        # on modality
        self.series = {
            "RTSTRUCT": self.rtstructs,
            "RTPLAN": self.rtplans,
            "RTDOSE": self.rtdoses,
            "SR": self.sr_files,
            "IMAGE": self.image_series
        }

        self.widget_item = None  # Study widget
        self.image_series_widgets = {}  # Dictionary of image series widgets
        self.rtstruct_widgets = {}  # Dictionary of RTSTRUCT widgets
        self.rtplan_widgets = {}  # Dictionary of RTPLAN widgets

    def add_series(self, series):
        """
        Adds a Series object to one of the patient's series dictionaries.
        :param series: A Series object.
        """
        series_type = series.get_series_type()
        if series_type in self.series:
            self.series[series_type][series.series_uid] = series
        else:
            self.series["IMAGE"][series.series_uid] = series

    def has_series(self, series_uid):
        """
        :param series_uid: A SeriesInstanceUID to check.
        :return: True if image series contains series_uid.
        """
        return series_uid in self.image_series

    def get_series(self, series_uid):
        """
        :param series_uid: SeriesID to check.
        :return: Series object if series found.
        """
        return self.image_series[series_uid] \
            if self.has_series(series_uid) else None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for series_type, series in self.series.items():
            for series_uid, image_series in series.items():
                filepaths += (image_series.get_files())
        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return f"Study: {self.study_description} (DICOM-RT: {'Y' if self.is_dicom_rt() else 'N'})"

    def is_dicom_rt(self):
        """
        :return: True if study can be considered DICOM-RT
        """

        rt_classes = {
            dicom_constants.CT_IMAGE,
            dicom_constants.RT_STRUCTURE_SET,
            dicom_constants.RT_DOSE,
            dicom_constants.RT_PLAN
        }

        contained_classes = set()
        for series_type, series in self.series.items():
            for series_uid, image_series in series.items():
                for image_uid, image in image_series.images.items():
                    contained_classes.add(image.class_id)

        return rt_classes == contained_classes

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        self.widget_item = DICOMWidgetItem(self.output_as_text(), self)

        # Add child widgets of Study following the hierarchy of objects
        # 1. Image series, 2. RTSTRUCT, 3. RTPLAN, 4. RTDOSE
        for series_uid, image_series in self.image_series.items():
            self.get_image_series_widget(series_uid, image_series)
        for series_uid, rtstruct in self.rtstructs.items():
            self.get_rtstruct_widget(rtstruct)
        for series_uid, rtplan in self.rtplans.items():
            self.get_rtplan_widget(rtplan)
        for series_uid, rtdose in self.rtdoses.items():
            self.get_rtdose_widgets(rtdose)
        for series_uid, sr_file in self.sr_files.items():
            self.get_sr_widgets(sr_file)

        return self.widget_item

    def get_image_series_widget(self, series_uid, image_series):
        """ Add a DICOMWidgetItem of an image series """
        self.image_series_widgets[series_uid] = image_series.get_widget_item()
        self.widget_item.addChild(self.image_series_widgets[series_uid])

    def get_rtstruct_widget(self, rtstruct):
        """ Add a DICOMWidgetItem of a RTSTRUCT """
        ref_image_series_uid = rtstruct.ref_image_series_uid
        rtstruct_instance_uid = rtstruct.get_instance_uid()
        self.rtstruct_widgets[rtstruct_instance_uid] = rtstruct.get_widget_item()

        # Check if the referenced image series exists in the dataset
        if ref_image_series_uid != "" and \
                ref_image_series_uid in self.image_series_widgets:
            self.image_series_widgets[ref_image_series_uid]. \
                addChild(self.rtstruct_widgets[rtstruct_instance_uid])
            return

        # Add the RTSTRUCT to the Study widget
        self.widget_item.addChild(self.rtstruct_widgets[rtstruct_instance_uid])

    def get_rtplan_widget(self, rtplan):
        """ Add a DICOMWidgetItem of a RTPLAN """
        ref_rtstruct_instance_uid = rtplan.ref_rtstruct_instance_uid
        rtplan_instance_uid = rtplan.get_instance_uid()
        self.rtplan_widgets[rtplan_instance_uid] = rtplan.get_widget_item()

        # Check if the referenced RTSTRUCT exists
        if ref_rtstruct_instance_uid:
            for series_uid, rtstruct in self.rtstructs.items():
                rtstruct_instance_uid = rtstruct.get_instance_uid()
                if ref_rtstruct_instance_uid == rtstruct_instance_uid:
                    self.rtstruct_widgets[rtstruct_instance_uid]. \
                        addChild(self.rtplan_widgets[rtplan_instance_uid])
                    return

        # Check if there is an image series with the same FrameOfReferenceUID
        if rtplan.frame_of_reference_uid:
            for series_uid, image_series in self.image_series.items():
                if rtplan.frame_of_reference_uid == \
                        image_series.frame_of_reference_uid:
                    empty_rtss = self.get_empty_widget("RTSTRUCT")
                    empty_rtss.addChild(
                        self.rtplan_widgets[rtplan_instance_uid])
                    self.image_series_widgets[series_uid].addChild(empty_rtss)
                    return

        # Add the RTPLAN to the Study widget
        self.widget_item.addChild(self.rtplan_widgets[rtplan_instance_uid])

    def get_rtdose_widgets(self, rtdose):
        """ Add a DICOMWidgetItem of a RTDOSE """
        ref_rtstruct_instance_uid = rtdose.ref_rtstruct_instance_uid
        ref_rtplan_instance_uid = rtdose.ref_rtplan_instance_uid
        rtdose_widget = rtdose.get_widget_item()

        # Check if the referenced RTPLAN exists in the dataset
        for series_uid, rtplan in self.rtplans.items():
            rtplan_instance_uid = rtplan.get_instance_uid()
            if ref_rtplan_instance_uid == rtplan_instance_uid:
                self.rtplan_widgets[rtplan_instance_uid].addChild(
                    rtdose_widget)
                return

        # Check if the referenced RTSTRUCT exists in the dataset or there is an
        # RTSTRUCT with the same FrameOfReferenceUID
        if ref_rtstruct_instance_uid != "" or \
                rtdose.frame_of_reference_uid != "":
            for series_uid, rtstruct in self.rtstructs.items():
                rtstruct_instance_uid = rtstruct.get_instance_uid()
                if (ref_rtstruct_instance_uid and
                    ref_rtstruct_instance_uid == rtstruct_instance_uid) or \
                        (rtdose.frame_of_reference_uid != "" and
                         rtdose.frame_of_reference_uid ==
                         rtstruct.frame_of_reference_uid):
                    empty_rtplan = self.get_empty_widget("RTPLAN")
                    empty_rtplan.addChild(rtdose_widget)
                    self.rtstruct_widgets[rtstruct_instance_uid]. \
                        addChild(empty_rtplan)
                    return

        # Check if there is an image series with the same FrameOfReferenceUID
        if rtdose.frame_of_reference_uid != "":
            for series_uid, image_series in self.image_series.items():
                if rtdose.frame_of_reference_uid == \
                        image_series.frame_of_reference_uid:
                    empty_rtplan = self.get_empty_widget("RTPLAN")
                    empty_rtplan.addChild(rtdose_widget)
                    empty_rtss = self.get_empty_widget("RTSTRUCT")
                    empty_rtss.addChild(empty_rtplan)
                    self.image_series_widgets[series_uid].addChild(empty_rtss)
                    return

        # Add the RTDOSE to the Study widget
        self.widget_item.addChild(rtdose_widget)

    def get_sr_widgets(self, sr_file):
        """ Add a DICOMWidgetItem of a SR file """
        sr_widget = sr_file.get_widget_item()

        # Check if there is an image series with the same FrameOfReferenceUID
        if sr_file.referenced_frame_of_reference_uid:
            for series_uid, image_series in self.image_series.items():
                if sr_file.referenced_frame_of_reference_uid == \
                        image_series.frame_of_reference_uid:
                    self.image_series_widgets[series_uid].addChild(sr_widget)
                    return

        # Add the SR file to the Study widget
        self.widget_item.addChild(sr_widget)

    def get_empty_widget(self, modality):
        """
        Create an empty widget to represent an object that does not present in
        the dataset
        :param modality: modality of the empty object
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(f"No matched {modality} was found.", None)
        return widget_item
