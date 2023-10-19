import os
from src.Model import CalculateDVHs
from src.Model import ImageLoading
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import pandas as pd
import numpy as np


class BatchProcessDVH2CSV(BatchProcess):
    """
    This class handles batch processing for the DVH2CSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for ISO2ROI
    allowed_classes = {
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
        },
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 output_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: output of the resulting .csv file.
        """
        # Call the parent class
        super(BatchProcessDVH2CSV, self).__init__(progress_callback,
                                                  interrupt_flag,
                                                  patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('rtss', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path
        self.filename = "DVHs_.csv"

    def start(self):
        """
        Goes through the steps of the DVH2CSV conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        # Check if the dataset is complete
        self.progress_callback.emit(("Checking dataset...", 40))

        # Attempt to get DVH data from RT Dose
        self.progress_callback.emit(("Attempting to get DVH from RTDOSE...",
                                     50))
        # Get DVH data
        raw_dvh = CalculateDVHs.rtdose2dvh()

        # If there is DVH data
        dvh_outdated = True
        if bool(raw_dvh):
            incomplete = raw_dvh["diff"]
            raw_dvh.pop("diff")

            if not incomplete:
                dvh_outdated = False
                self.progress_callback.emit(("DVH data in RT Dose.", 80))
        else:
            raw_dvh.pop("diff")

        if dvh_outdated:
            # Calculate DVH if not in RT Dose
            self.progress_callback.emit(("Calculating DVH...", 60))
            read_data_dict = self.patient_dict_container.dataset
            dataset_rtss = self.patient_dict_container.dataset['rtss']
            dataset_rtdose = self.patient_dict_container.dataset['rtdose']
            rois = self.patient_dict_container.get("rois")
            try:
                dict_thickness = \
                    ImageLoading.get_thickness_dict(dataset_rtss,
                                                    read_data_dict)
                raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose,
                                                 rois, dict_thickness,
                                                 self.interrupt_flag)
            except TypeError:
                self.summary = "DVH_TYPE_ERROR"
                return False

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Export DVH to CSV
        self.progress_callback.emit(("Exporting DVH to CSV...", 90))

        # Get path to save to
        path = self.output_path + '/CSV/'

        # Get patient ID
        patient_id = self.patient_dict_container.dataset['rtss'].PatientID

        # Make CSV directory if it doesn't exist
        if not os.path.isdir(path):
            os.mkdir(path)

        # Save the DVH to a CSV file
        self.progress_callback.emit(("Exporting DVH to RT Dose...", 95))
        self.dvh2csv(raw_dvh, path, self.filename, patient_id)

        # Save the DVH to the RT Dose
        CalculateDVHs.dvh2rtdose(raw_dvh)

        return True

    def dvh2csv(self, dict_dvh, path, csv_name, patient_id):
        """
        Export dvh data to csv file.
        Append to existing file
        :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
        :param path: Target path of CSV export
        :param csv_name: CSV file name
        :param patient_id: Patient Identifier
        """
        # full path of the target csv file
        tar_path = path + csv_name

        create_header = not os.path.isfile(tar_path)

        dvh_csv_list = []

        csv_header = []
        csv_header.append('Patient ID')
        csv_header.append('ROI')
        csv_header.append('Volume (mL)')

        # DVH.CSV EXPORT
        
        #Row in centiGray cGy
        for i in dict_dvh:
            dvh_roi_list = []
            dvh = dict_dvh[i]
            name = dvh.name
            volume = dvh.volume
            dvh_roi_list.append(patient_id)
            dvh_roi_list.append(name)
            dvh_roi_list.append(volume)
            
            dose = dvh.relative_volume.counts
            
            trough_i = 0
            peak_i = 0
            for percent in np.arange(100, -0.5, -0.5):
                last_volume = -1
                for cgy in range(trough_i, len(dose), 10):
                    trough_i = cgy
                    if dose[cgy] == percent:
                        last_volume = cgy
                    elif dose[cgy] > percent:
                        peak_i = cgy
                    elif dose[cgy] < percent:
                        break
                if last_volume == -1 and peak_i != 0:
                    if dose[peak_i] != dose[trough_i]:
                        volume_per_drop = -10 * (dose[peak_i] - dose[trough_i])/(peak_i - trough_i)
                        per_drop = dose[peak_i] - percent
                        substract_amount = per_drop/volume_per_drop * 10
                        last_volume = trough_i - substract_amount
                    else:
                        last_volume = trough_i
                if last_volume != -1:
                    dvh_roi_list.append(str(round(last_volume)))
                else:
                    dvh_roi_list.append('')
            dvh_csv_list.append(dvh_roi_list)
                
        #Column in percentage %
        for i in np.arange(100, -0.5, -0.5):
            csv_header.append(str(i) + '%')

        # Convert the list into pandas dataframe, with 2 digit rounding.
        pddf_csv = pd.DataFrame(dvh_csv_list, columns=csv_header).round(2)
        # Fill empty blocks with 0.0
        pddf_csv.fillna(0.0, inplace=True)
        pddf_csv.set_index('Patient ID', inplace=True)
        # Convert and export pandas dataframe to CSV file
        pddf_csv.to_csv(tar_path, mode='a', header=create_header)

    def set_filename(self, name):
        if name != '':
            self.filename = name
        else:
            self.filename = "DVHs_.csv"
