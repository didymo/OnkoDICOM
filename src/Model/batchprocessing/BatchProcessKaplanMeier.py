import kaplanmeier as km
#import matplotlib as mp1
#mp1.use("TkAgg")
from matplotlib import pyplot as plt
import pandas as pd
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import logging
import os
import numpy as np

class BatchProcessKaplanMeier(BatchProcess):
    """
    This class handles batch processing for the Clinical Data 2 CSV
    process. Inherits from the BatchProcessing class.
    """

    def __init__(self,
                 progress_callback,
                 interrupt_flag,
                 data_dict,
                 kaplanmeier_target_col,
                 kaplanmeier_duration_of_life_col,
                 kaplanmeier_alive_or_dead_col):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: Path of the output CSV file.
        """
        # Call the parent class
        super(BatchProcessKaplanMeier, self).__init__(progress_callback,
                                                             interrupt_flag,
                                                             None)

        # Set class variables
        self.kaplanmeier_target_col = kaplanmeier_target_col
        self.kaplanmeier_duration_of_life_col = kaplanmeier_duration_of_life_col
        self.kaplanmeier_alive_or_dead_col = kaplanmeier_alive_or_dead_col
        self.my_plt = None
        self.data_dict = data_dict

    def start(self):
        """
        Goes through the steps of the ClinicalData-SR2CSV conversion.
        :return: True if successful, False if not.
        """
        self.progress_callback.emit(("Writing clinical data to CSV...", 80))
        self.plot(
            data_dict,
            self.kaplanmeier_target_col,
            self.kaplanmeier_duration_of_life_col,
            self.kaplanmeier_alive_or_dead_col)
        
        return True

    def get_image(self):

    def plot(self,data_dict, target, duration_of_life, alive_or_dead):
        """
            Creates plot based off input columns
        """
        try:
            logging.debug("Creating/Displaying plot")
            # creates dataframe based on patient records
            df = pd.DataFrame.from_dict(self.data_dict)
            # creates input parameters for the km.fit() function
            time_event = df[duration_of_life]
            censoring = df[alive_or_dead]
            y = df[target]
            # create kaplanmeier plot
            results = km.fit(time_event, censoring, y)
            km.plot(results, cmap='Set1', cii_lines='dense', cii_alpha=0.10)
            # specifies plot layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.903,
                                bottom=0.423,
                                left=0.085,
                                right=0.965,
                                hspace=0.2,
                                wspace=0.2)

            #self.my_plt = plt
            #plt.show()
            try:
                # Create Pyradiomics Directory
                os.mkdir('./data/kaplan')

            except FileExistsError:
                logging.debug('Directory already exists')
            plt.savefig('./data/kaplan/plot.png')

        except:

            logging.debug("failed to create plot")
            self.summary = "INTERRUPT"
