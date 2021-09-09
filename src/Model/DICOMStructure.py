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
        widget_item.setFlags(widget_item.flags()
                             | Qt.ItemIsAutoTristate
                             | Qt.ItemIsUserCheckable)

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
        self.image_series = {}
        self.rtstruct = {}
        self.rtplan = {}
        self.rtdose = {}

    def add_series(self, series):
        """
        Adds a Series object to one of the patient's series dictionaries.
        :param series: A Series object.
        """
        series_type = series.get_series_type()
        if series_type == "RTSTRUCT":
            if series.referenced_image_series_uid in self.rtstruct:
                self.rtstruct[series.referenced_image_series_uid].append(
                    series)
            else:
                self.rtstruct[series.referenced_image_series_uid] = [
                    series]
        elif series_type == "RTPLAN":
            if series.referenced_rtss_uid in self.rtplan:
                self.rtplan[series.referenced_rtss_uid].append(series)
            else:
                self.rtplan[series.referenced_rtss_uid] = [series]
        elif series_type == "RTDOSE":
            if series.refenced_rtplan_uid in self.rtdose:
                self.rtdose[series.refenced_rtplan_uid].append(series)
            else:
                self.rtdose[series.refenced_rtplan_uid] = [series]
        else:
            self.image_series[series.series_uid] = series

    def has_series(self, series_uid):
        """
        :param series_uid: A SeriesInstanceUID to check.
        :return: True if series contains series_uid.
        """
        return series_uid in self.image_series

    def get_series(self, series_uid):
        """
        :param series_uid: SeriesID to check.
        :return: Series object if series found.
        """
        if self.has_series(series_uid):
            return self.image_series[series_uid]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for series_uid, series in self.image_series.items():
            filepaths += (series.get_files())

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
        for series_uid, series in self.image_series.items():
            for image_uid, image in series.images.items():
                if image.class_id not in contained_classes:
                    contained_classes.append(image.class_id)

        return sorted(rt_classes) == sorted(contained_classes)

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags()
                             | Qt.ItemIsAutoTristate
                             | Qt.ItemIsUserCheckable)
        image_series_widgets = {}
        rtstruct_widgets = {}
        rtplan_widgets = {}
        for image_uid, image in self.image_series.items():
            image_series_widgets[image_uid] = image.get_widget_item()
            widget_item.addChild(image_series_widgets[image_uid])

        for image_uid, rtstructs in self.rtstruct.items():
            for rtstruct in rtstructs:
                rtstruct_widgets[rtstruct.get_instance_uid()] = rtstruct.get_widget_item()
                if image_uid != "" and image_uid in image_series_widgets:
                    image_series_widgets[image_uid].addChild(rtstruct_widgets[rtstruct.get_instance_uid()])
                else:
                    widget_item.addChild(rtstruct_widgets[rtstruct.get_instance_uid()])

        for rtstruct_uid, rtplans in self.rtplan.items():
            for rtplan in rtplans:
                rtplan_widgets[rtplan.get_instance_uid()] = rtplan.get_widget_item()
                found_rtss = False
                for image_uid, rtstructs in self.rtstruct.items():
                    for rtstruct in rtstructs:
                        for id, image in rtstruct.images.items():
                            if rtstruct_uid == id:
                                rtstruct_widgets[rtstruct_uid].addChild(rtplan_widgets[rtplan.get_instance_uid()])
                                found_rtss = True
                                break
                if not found_rtss:
                    found_image_series = False
                    if rtplan.frame_of_reference_uid != "":
                        for image_uid, image in self.image_series.items():
                            if rtplan.frame_of_reference_uid == image.frame_of_reference_uid:
                                temp_rtss = self.get_empty_widget("RTSTRUCT")
                                temp_rtss.addChild(rtplan_widgets[rtplan.get_instance_uid()])
                                image_series_widgets[image_uid].addChild(temp_rtss)
                                found_image_series = True
                                break
                    if not found_image_series:
                        widget_item.addChild(rtplan_widgets[rtplan.get_instance_uid()])

        for rtplan_uid, rtdoses in self.rtdose.items():
            for rtdose in rtdoses:
                rtdose_widget = rtdose.get_widget_item()
                found_rtplan = False
                for rtstruct_uid, rtplans in self.rtplan.items():
                    for rtplan in rtplans:
                        for id, image in rtplan.images.items():
                            if rtplan_uid == id:
                                rtplan_widgets[rtplan_uid].addChild(rtdose_widget)
                                found_rtplan = True
                                break

                if not found_rtplan:
                    found_rtstruct = False
                    if rtdose.referenced_rtss_uid != "" or rtdose.frame_of_reference_uid != "":
                        for image_uid, rtstructs in self.rtstruct.items():
                            for rtstruct in rtstructs:
                                for id, image in rtstruct.images.items():
                                    if (rtdose.referenced_rtss_uid != "" and rtdose.referenced_rtss_uid == id) or \
                                            (rtdose.frame_of_reference_uid != "" and rtdose.frame_of_reference_uid == rtstruct.frame_of_reference_uid):
                                        temp_rtplan = self.get_empty_widget("RTPLAN")
                                        temp_rtplan.addChild(rtdose_widget)
                                        rtstruct_widgets[rtstruct.series_uid].addChild(temp_rtplan)
                                        found_rtstruct = True
                                        break

                    if not found_rtstruct:
                        found_series = False
                        if rtdose.frame_of_reference_uid != "":
                            for image_uid, image in self.image_series.items():
                                if rtdose.frame_of_reference_uid == image.frame_of_reference_uid:
                                    temp_rtplan = self.get_empty_widget("RTPLAN")
                                    temp_rtplan.addChild(rtdose_widget)
                                    temp_rtss = self.get_empty_widget("RTSTRUCT")
                                    temp_rtss.addChild(temp_rtplan)
                                    image_series_widgets[image_uid].addChild(temp_rtss)
                                    found_series = True
                                    break

                        if not found_series:
                            widget_item.addChild(rtdose_widget)

        return widget_item

    def get_empty_widget(self, name):
        widget_item = DICOMWidgetItem("No matched " + name + " was found.", self)
        widget_item.setFlags(widget_item.flags()
                             | Qt.ItemIsAutoTristate
                             | Qt.ItemIsUserCheckable)
        widget_item.setCheckState(0, Qt.Unchecked)
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

    def get_instance_uid(self):
        if len(self.images) == 1:
            for id, image in self.images.items():
                return id

    def add_image(self, image):
        """
        Adds an Image object to the patient's dictionary of images.
        :param image:  An Image object.
        """
        self.images[image.image_uid] = image

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

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags()
                             | Qt.ItemIsAutoTristate
                             | Qt.ItemIsUserCheckable)
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
