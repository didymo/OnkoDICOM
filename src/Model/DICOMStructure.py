from PySide6.QtCore import Qt

from src.Model.DICOMWidgetItem import DICOMWidgetItem


class DICOMStructure:
    """
    A class representing the structure of the given DICOM files. Used by the
    open patient window to generate the tree structure of the DICOM set.
    Creates a hierarchy of Patient -> can have many Studies -> which can
    have many Series -> which can have many Images.
    """

    def __init__(self):
        """
        patients: A dictionary of Patient objects.
        """
        self.patients = {}

    def add_patient(self, patient):
        """
        Add a Patient object to the dictionary of patients.
        :param patient: A Patient object.
        """
        self.patients[patient.patient_id] = patient

    def has_patient(self, patient_id):
        """
        :param patient_id: PatientID to check.
        :return: True if patients contains patient_id.
        """
        return patient_id in self.patients

    def get_patient(self, patient_id):
        """
        :param patient_id: PatientID to check.
        :return: Patient object if patient found.
        """
        if self.has_patient(patient_id):
            return self.patients[patient_id]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for patient_id, patient in self.patients.items():
            filepaths += (patient.get_files())

        return filepaths

    def get_tree_items_list(self):
        """
        :return: A list of QTreeWidgetItems based on the DICOMStructure object.
        """
        return [patient.get_widget_item()
                for patient_id, patient in self.patients.items()]


class Patient:

    def __init__(self, patient_id, patient_name):
        """
        studies: A dictionary of Study objects.
        :param patient_id: PatientID in DICOM standard.
        """
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.studies = {}

    def add_study(self, study):
        """
        Adds a Study object to the patient's dictionary of studies.
        :param study: A Study object.
        """
        self.studies[study.study_uid] = study

    def has_study(self, study_uid):
        """
        :param study_uid: StudyInstanceUID to check.
        :return: True if studies contains study_uid
        """
        return study_uid in self.studies

    def get_study(self, study_uid):
        """
        :param study_uid: StudyID to check.
        :return: Study object if study found.
        """
        if self.has_study(study_uid):
            return self.studies[study_uid]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for study_uid, study in self.studies.items():
            filepaths += (study.get_files())

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Patient: %s (%s)" % (self.patient_name, self.patient_id)

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)

        # Add all children of this object as children of the widget item.
        for study_uid, study in self.studies.items():
            widget_item.addChild(study.get_widget_item())
        return widget_item


class Study:

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
        self.image_series = {}

        # Dictionary contains all series, used to quickly add new series based
        # on modality
        self.series = {
            "RTSTRUCT": self.rtstructs,
            "RTPLAN": self.rtplans,
            "RTDOSE": self.rtdoses,
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
        return "Study: %s (DICOM-RT: %s)" % (
            self.study_description, "Y" if self.is_dicom_rt() else "N")

    def is_dicom_rt(self):
        """
        :return: True if study can be considered DICOM-RT
        """
        rt_classes = ["1.2.840.10008.5.1.4.1.1.2",          # CT Image
                      "1.2.840.10008.5.1.4.1.1.481.3",      # RT Structure Set
                      "1.2.840.10008.5.1.4.1.1.481.2",      # RT Dose
                      "1.2.840.10008.5.1.4.1.1.481.5"]      # RT Plan

        contained_classes = []
        for series_type, series in self.series.items():
            for series_uid, image_series in series.items():
                for image_uid, image in image_series.images.items():
                    if image.class_id not in contained_classes:
                        contained_classes.append(image.class_id)

        return sorted(rt_classes) == sorted(contained_classes)

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

        return self.widget_item

    def get_image_series_widget(self, series_uid, image_series):
        """ Add a DICOMWidgetItem of an image series """
        self.image_series_widgets[series_uid] = image_series.get_widget_item()
        self.image_series_widgets[series_uid].setWhatsThis(0, "IMAGE")
        self.widget_item.addChild(self.image_series_widgets[series_uid])

    def get_rtstruct_widget(self, rtstruct):
        """ Add a DICOMWidgetItem of a RTSTRUCT """
        ref_image_series_uid = rtstruct.ref_image_series_uid
        rtstruct_instance_uid = rtstruct.get_instance_uid()
        self.rtstruct_widgets[rtstruct_instance_uid] = \
            rtstruct.get_widget_item()
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
                    self.rtstruct_widgets[rtstruct_instance_uid].\
                        addChild(self.rtplan_widgets[rtplan_instance_uid])
                    return

        # Check if there is an image series with the same FrameOfReferenceUID
        if rtplan.frame_of_reference_uid:
            for series_uid, image_series in self.image_series.items():
                if rtplan.frame_of_reference_uid == image_series.frame_of_reference_uid:
                    empty_rtss = self.get_empty_widget("RTSTRUCT")
                    empty_rtss.addChild(self.rtplan_widgets[rtplan_instance_uid])
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
                self.rtplan_widgets[rtplan_instance_uid].addChild(rtdose_widget)
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

    def get_empty_widget(self, modality):
        """
        Create an empty widget to represent an object that does not present in
        the dataset
        :param modality: modality of the empty object
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem("No matched " + modality + " was found.",
                                      None)
        return widget_item


class Series:

    def __init__(self, series_uid):
        """
        images: A dictionary of Image objects.
        :param series_uid: SeriesInstanceUID in DICOM standard.
        """
        self.series_uid = series_uid
        self.series_description = None
        self.images = {}
        self.frame_of_reference_uid = ""

    def add_image(self, image):
        """
        Adds an Image object to the patient's dictionary of images.
        :param image:  An Image object.
        """
        self.images[image.image_uid] = image

    def add_referenced_objects(self, dicom_file):
        if "FrameOfReferenceUID" in dicom_file:
            self.frame_of_reference_uid = dicom_file.FrameOfReferenceUID
        if dicom_file.Modality == "RTSTRUCT":
            self.add_referenced_image_series(dicom_file)
        elif dicom_file.Modality == "RTPLAN":
            self.add_referenced_rtstruct(dicom_file)
        elif dicom_file.Modality == "RTDOSE":
            self.add_referenced_rtstruct(dicom_file)
            self.add_referenced_rtplan(dicom_file)

    def add_referenced_image_series(self, dicom_file):
        if "ReferencedFrameOfReferenceSequence" in dicom_file:
            ref_frame = dicom_file.ReferencedFrameOfReferenceSequence
            if "RTReferencedStudySequence" in ref_frame[0]:
                ref_study = ref_frame[0].RTReferencedStudySequence[0]
                if "RTReferencedSeriesSequence" in ref_study:
                    if "SeriesInstanceUID" in \
                            ref_study.RTReferencedSeriesSequence[0]:
                        ref_series = ref_study.RTReferencedSeriesSequence[0]
                        self.ref_image_series_uid = \
                            ref_series.SeriesInstanceUID
        else:
            self.ref_image_series_uid = ''

    def add_referenced_rtstruct(self, dicom_file):
        if "ReferencedStructureSetSequence" in dicom_file:
            self.ref_rtstruct_instance_uid = \
                dicom_file.ReferencedStructureSetSequence[
                    0].ReferencedSOPInstanceUID
        else:
            self.ref_rtstruct_instance_uid = ''

    def add_referenced_rtplan(self, dicom_file):
        if "ReferencedRTPlanSequence" in dicom_file:
            self.ref_rtplan_instance_uid = \
                dicom_file.ReferencedRTPlanSequence[
                    0].ReferencedSOPInstanceUID
        else:
            self.ref_rtplan_instance_uid = ''

    def has_image(self, image_uid):
        """
        :param image_uid: A SOPInstanceUID to check.
        :return: True if images contains image_uid.
        """
        return image_uid in self.images

    def get_image(self, image_uid):
        """
        :param image_uid: ImageID to check
        :return: Image object if Image found.
        """
        if self.get_image(image_uid):
            return self.images[image_uid]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for image_uid, image in self.images.items():
            filepaths += [image.path]

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Series: %s (%s, %s images)" % (
            self.series_description, self.get_series_type(), len(self.images))

    def get_series_type(self):
        """
        :return: List of string or single string containing modalities of all
        images in the series.
        """
        series_types = []
        for image_uid, image in self.images.items():
            if image.modality not in series_types:
                series_types.append(image.modality)
        return series_types if len(series_types) > 1 else series_types[0]

    def get_instance_uid(self):
        """
        :return: List of string or single string containing instance uid of all
        images in the series.
        """
        instance_uid = []
        for image_instance_uid, image in self.images.items():
            instance_uid.append(image_instance_uid)
        return instance_uid if len(instance_uid) > 1 else instance_uid[0]

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsUserCheckable)
        widget_item.setCheckState(0, Qt.Unchecked)
        return widget_item


class Image:

    def __init__(self, path, image_uid, class_id, modality):
        """
        image_uid: SOPInstanceUID in DICOM standard.
        :param path: Path of the DICOM file.
        """
        self.path = path
        self.image_uid = image_uid
        self.class_id = class_id
        self.modality = modality

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Image: %s | Path: %s" % (self.image_uid, self.path)
