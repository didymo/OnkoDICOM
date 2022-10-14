import os
import platform
import logging
from radiomics import featureextractor
from src.Model import Radiomics
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess
import pandas as pd


class BatchProcessPyRad2CSV(BatchProcess):
    """
    This class handles batch processing for the PyRadCSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for PyRadCSV
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
        super(BatchProcessPyRad2CSV, self).__init__(progress_callback,
                                                   interrupt_flag,
                                                   patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = 'rtss'.split()
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path
        self.filename = "Pyradiomics_.csv"

    def start(self):
        """
        Goes through the steps of the PyRadCSV conversion.
        """
        logging.debug("start pyrad-sr2csv")

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        rtss_path = self.patient_dict_container.filepaths.get('rtss')
        patient_id = self.patient_dict_container.dataset.get('rtss').PatientID
        patient_id = Radiomics.clean_patient_id(patient_id)
        patient_path = self.patient_dict_container.path
        output_csv_path = self.output_path.joinpath('CSV')

        if not os.path.exists(patient_path + '/Pyradiomics-SR.dcm'):
            self.patient_dict_container.clear()
            self.summary = "NO_SR"
            return False

        # If folder does not exist
        if not os.path.exists(output_csv_path):
            # Create folder
            os.makedirs(output_csv_path)

        self.progress_callback.emit(("PyRad-SR to CSV..", 70))

        # Convert pyradsr to dataframe
        srfile = open(patient_path + '/Pyradiomics-SR.dcm', 'rb')
        contents = srfile.readlines()
        pre_df = []

        # This while loop is to get the next line after the one with Hash ID in it 
        i = 0
        while i != len(contents):
            if b'Hash' in contents[i]:
                tick = i
                break
            i += 1
        
        i = 0
        while i != (len(contents)-1):
            if i == 0:
                # Setup headers for DataFrame
                start = str(contents).find("Hash")
                end = str(contents).find("original_ngtdm_Strength")
                # +23 to make sure the whole original_ngtdm_Strength is in the last header
                temp = str(contents)[start:end+23]
                headers = temp.split(",")
                i = tick

            else:
                # Formatting for DataFrame
                # Certain headers require data within brackets hence why indexes are called so that 
                # the data can be extracted correctly and when the csv file is viewed all values
                # correlate to their relative header
                temp = str(contents[i])[2:]
                srdata = temp[:len(temp)-4]
                srdata = srdata.split(",", 8)
                del srdata[8]

                end = temp[:len(temp)-4]
                end = end.rsplit(",", 107)
                del end[0]

                preIndex = temp.find("{")
                postIndex = temp.find("}")
                mid = temp[preIndex:postIndex+1]
                srdata.append(mid)

                mid = temp[postIndex+2:].split(",")
                mid = mid[0:3]

                preIndex = temp.find("(")
                postIndex = temp.find(")")
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                preIndex = temp.find("(", postIndex+1)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                midContent = temp[postIndex+2:].split(",")
                mid += midContent[0:4]

                preIndex = temp.find("(", postIndex)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                preIndex = temp.find("(", postIndex)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                preIndex = temp.find("(", postIndex)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                midContent = temp[postIndex+2:].split(",")
                mid += midContent[0:2]

                preIndex = temp.find("(", postIndex)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                preIndex = temp.find("(", postIndex)
                postIndex = temp.find(")", preIndex)
                midContent = temp[preIndex:postIndex+1]
                mid.append(midContent)

                srdata += mid + end
                pre_df.append(srdata)
            
            i += 1

        radiomics_df = pd.DataFrame(pre_df)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if radiomics_df is None:
            self.summary = "PYRAD_NO_DF"
            return False
        
        # Convert the dataframe to CSV file
        self.progress_callback.emit(("Converting to CSV..", 90))
        # If folder does not exist
        if not os.path.exists(output_csv_path):
            # Create folder
            os.makedirs(output_csv_path)
        target_path = output_csv_path.joinpath(self.filename)
        create_header = not os.path.isfile(target_path)
        if create_header:
            # Export dataframe as csv
            radiomics_df.to_csv(target_path, mode='a', index=False, header=headers)
        else:
            # Export dataframe as csv
            radiomics_df.to_csv(target_path, mode='a', index=False, header=False)
        return True

        logging.debug("pyrad-sr2csv success")

    def set_filename(self, name):
        if name != '':
            self.filename = name
        else:
            self.filename = "Pyradiomics_.csv"
