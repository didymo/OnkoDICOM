import glob
import os
import re
import numpy as np
from PyQt5.QtCore import QFileInfo
from dicompylercore import dvhcalc, dvh, dicomparser
import pydicom
from PyQt5 import QtCore



class Extended(QtCore.QThread):
    """
    For running copy operation
    """

    copied_percent_signal = QtCore.pyqtSignal(int)
    incorrect_directory_signal = QtCore.pyqtSignal()
    missing_files_signal = QtCore.pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.copied = 0
        self.file_size = QFileInfo(path).size()
        self.path = path
        self.read_data_dict = {}

        # Data contains file paths
        # Key is int for ct images and str (rtdose, rtss, rtplan) for RT files
        self.file_names_dict = {}
        self.previous = 0

    def run(self):
        self.get_datasets(self.path, self.my_callback)

        if not self.file_names_dict:
            self.incorrect_directory_signal.emit()

        elif 'rtss' not in self.file_names_dict:
            if 'rtdose' not in self.file_names_dict:
                self.missing_files_signal.emit('RTStruct and RTDose files not found in selected directory')
            else:
                self.missing_files_signal.emit('RTStruct file not found in selected directory')
        else:
            self.file_rtss = self.file_names_dict['rtss']
            self.file_rtdose = self.file_names_dict['rtdose']
            self.dataset_rtss = pydicom.dcmread(self.file_rtss)
            self.dataset_rtdose = pydicom.dcmread(self.file_rtdose)
            self.rois = self.get_roi_info(self.dataset_rtss, self.my_callback)
            self.raw_dvh = self.calc_dvhs(self.dataset_rtss, self.dataset_rtdose, self.rois, self.my_callback)
            self.dvh_x_y = self.converge_to_O_dvh(self.raw_dvh, self.my_callback)
            if self.previous <100:
                for i in range(self.previous,101):
                    self.copied_percent_signal.emit(i)


    def my_callback(self, temp_file_size):
        percent = int(temp_file_size/self.file_size*10)
        if percent < self.previous or percent == 100:
            percent = self.previous
        elif percent == self.previous and percent < 98:
            percent +=1
        elif percent == self.previous:
            percent += 1
        self.copied_percent_signal.emit(percent)
        self.previous = percent

    def natural_sort(self,file_list):
        # Logger info
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        return sorted(file_list, key=alphanum_key)


    def get_datasets(self,path, callback):
        """
        :param path: str
        :return read_data_dict: dict
        :return file_names_dict: dict
        """

        # Data contains data read from files
        # Key is int for ct images and str (rtdose, rtss, rtplan) for RT files
        self.read_data_dict = {}

        # Data contains file paths
        # Key is int for ct images and str (rtdose, rtss, rtplan) for RT files
        self.file_names_dict = {}

        # Sort files based on name
        dcm_files = self.natural_sort(glob.glob(path + '/*'))
        i = 0 # For key values for ct images

        # For each file in path

        for file in dcm_files:
            # If file exists and the first two letters in the name are CT, RD, RP, RS, or RT
            if os.path.isfile(file) and os.path.basename(file)[0:2].upper() in ['CT', 'RD', 'RP', 'RS', 'RT']:
                try:
                    read_file = pydicom.dcmread(file)
                except:
                    pass
                else:    
                    if read_file.Modality == 'CT':
                        self.read_data_dict[i] = read_file
                        self.file_names_dict[i] = file
                        i += 1
                    elif read_file.Modality == 'RTSTRUCT':
                        self.read_data_dict['rtss'] = read_file
                        self.file_names_dict['rtss'] = file
                    elif read_file.Modality == 'RTDOSE':
                        self.read_data_dict['rtdose'] = read_file
                        self.file_names_dict['rtdose'] = file
                    elif read_file.Modality == 'RTPLAN':
                        self.read_data_dict['rtplan'] = read_file
                        self.file_names_dict['rtplan'] = file
                    self.copied += len(read_file)
                    callback(self.copied)

        return self.read_data_dict, self.file_names_dict

    def get_roi_info(self, ds_rtss, callback):
        dict_roi = {}
        for sequence in ds_rtss.StructureSetROISequence:
            dict_temp = {}
            dict_temp['uid'] = sequence.ReferencedFrameOfReferenceUID
            dict_temp['name'] = sequence.ROIName
            dict_temp['algorithm'] = sequence.ROIGenerationAlgorithm
            dict_roi[sequence.ROINumber] = dict_temp
            self.copied += len( dict_roi[sequence.ROINumber])
            callback(self.copied)
        return dict_roi


    # Return a dictionary of all the DVHs of all the ROIs of the patient
    # Return value: dict
    # {"1": dvh}
    # "1" is the ID of the ROI
    # dvh is a data type defined in dicompyler-core
    # For dvh plotting example with matplotlib, see: dvh_plot()
    def calc_dvhs(self, rtss, dose, dict_roi, callback, dose_limit=None):
        dict_dvh = {}
        for roi in dict_roi:
            # dicompylercore.dvhcalc.get_dvh(structure, dose, roi,
            #                                   limit=None, calculate_full_volume=True, use_structure_extents=False,
            #                                   interpolation_resolution=None, interpolation_segments_between_planes=0,
            #                                   thickness=None, callback=None)
            dict_dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)
            self.copied += 0.01*self.file_size
            callback(self.copied)
        return dict_dvh


    # Deal with the case where the last value of the DVH is not 0
    # Return a dictionary of bincenters (x axis of DVH) and counts (y value of DVH)
    # Return value: dict
    # {"1": {"bincenters": bincenters ; "counts": counts}}
    # "1" is the ID of the ROI
    def converge_to_O_dvh(self, dict_dvh, callback):
        res = {}
        zeros = np.zeros(3)
        for roi in dict_dvh:
            res[roi] = {}
            dvh = dict_dvh[roi]

            # The last value of DVH is not equal to 0
            if dvh.counts[-1] != 0:
                tmp_bincenters = []
                for i in range(3):
                    tmp_bincenters.append(dvh.bincenters[-1]+i)

                tmp_bincenters = np.array(tmp_bincenters)
                tmp_bincenters = np.concatenate((dvh.bincenters.flatten(), tmp_bincenters))
                bincenters = np.array(tmp_bincenters)
                counts = np.concatenate((dvh.counts.flatten(), np.array(zeros)))

            # The last value of DVH is equal to 0
            else:
                bincenters = dvh.bincenters
                counts = dvh.counts

            res[roi]['bincenters'] = bincenters
            res[roi]['counts'] = counts
        self.copied += len(res)
        callback(self.copied)
        return res

