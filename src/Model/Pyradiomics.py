"""
This file contains the functionality required for the pyradiomics analysis
"""

import os
import pandas as pd
import SimpleITK as sitk
from pydicom import dcmread
from radiomics import featureextractor
from src.Model.LoadPatients import get_datasets


def convert_to_nrrd(path, nrrd_file_path):
    """ 
    Convert dicom files to nrrd.
    
    :param path:            Path to patient directory (str)
    
    :param nrrd_file_path:  Path to nrrd folder (str)
    """
    cmd_for_nrrd = 'plastimatch convert --input ' + path + \
        ' --output-img ' + nrrd_file_path + ' 1>' + path + '/NUL'
    cmd_del_nul = 'rm ' + path + '/NUL'
    # reader = sitk.ImageSeriesReader()
    # dicomReader = reader.GetGDCMSeriesFileNames(path)
    # reader.SetFileNames(dicomReader)
    # dicoms = reader.Execute()
    # sitk.WriteImage(dicoms, nrrd_file_path)
    os.system(cmd_for_nrrd)
    os.system(cmd_del_nul)


def convert_rois_to_nrrd(path, rtss_path, mask_folder_path):
    """ 
    Convert rtstruct to nrrd

    :param path:                Path to patient directory (str)
    
    :param rtss_path:           Path to RT-Struct file (str)

    :param mask_folder_path:    Folder to which the segmentation masks will be saved(str)
    """
    # Each ROI is saved in separate nrrd files
    cmd_for_segmask = 'plastimatch convert --input ' + rtss_path + ' --output-prefix ' + \
        mask_folder_path + ' --prefix-format nrrd --referenced-ct ' + \
        path + ' 1>' + path + '/NUL'
    cmd_del_nul = 'rm ' + path + '/NUL'
    os.system(cmd_for_segmask)
    os.system(cmd_del_nul)


def get_radiomics_df(path, patient_hash, nrrd_file_path, mask_folder_path):
    # Initialize feature extractor using default pyradiomics settings
    # Default features:
    #   first order, glcm, gldm, glrlm, glszm, ngtdm, shape
    # Default settings:
    #   'minimumROIDimensions': 2, 'minimumROISize': None, 'normalize': False,
    #   'normalizeScale': 1, 'removeOutliers': None, 'resampledPixelSpacing': None,
    #   'interpolator': 'sitkBSpline', 'preCrop': False, 'padDistance': 5, 'distances': [1],
    #   'force2D': False, 'force2Ddimension': 0, 'resegmentRange': None, 'label': 1,
    #   'additionalInfo': True
    extractor = featureextractor.RadiomicsFeatureExtractor()

    print("Calculating features")

    # Contains the features for all the ROI
    all_features = []  
    # CSV headers
    radiomics_headers = []  
    feature_vector = ''

    for file in os.listdir(mask_folder_path):
        # Contains features for current ROI
        roi_features = []  
        roi_features.append(patient_hash)
        roi_features.append(path)
        # Full path of ROI nrrd file
        mask_name = mask_folder_path + '/' + file  
        # Name of ROI
        image_id = file.split('.')[0]  
        feature_vector = extractor.execute(nrrd_file_path, mask_name)
        roi_features.append(image_id)

        # Add first order features to list
        for feature_name in feature_vector.keys():  
            roi_features.append(feature_vector[feature_name])

        all_features.append(roi_features)

    radiomics_headers.append('Hash ID')
    radiomics_headers.append('Directory Path')
    radiomics_headers.append('ROI')

    # Extract column/feature names
    for feature_name in feature_vector.keys():
        radiomics_headers.append(feature_name)

    # Convert into dataframe
    radiomics_df = pd.DataFrame(all_features, columns=radiomics_headers)

    radiomics_df.set_index('Hash ID', inplace=True)

    return radiomics_df


def convert_df_to_csv(radiomics_df, patient_hash, csv_path):
    # If folder does not exist
    if not os.path.exists(csv_path):  
        # Create folder
        os.makedirs(csv_path)  

    # Export dataframe as csv
    radiomics_df.to_csv(csv_path + 'Pyradiomics_' +
                        patient_hash + '.csv')


def pyradiomics(path, filepaths, target_path=None):
    """
    Generate pyradiomics spreadsheet
    """

    ct_file = dcmread(filepaths[0], force=True)
    rtss_path = filepaths['rtss']

    if target_path is None:
        patient_hash = os.path.basename(ct_file.PatientID)
        # Name of nrrd file
        nrrd_file_name = patient_hash + '.nrrd'  
        # Location of folder where nrrd file saved
        nrrd_folder_path = path + '/nrrd/'
        # Location of folder where pyradiomics output saved
        csv_path = path + '/CSV/'
    else:
        patient_hash = os.path.basename(target_path)
        # Name of nrrd file
        nrrd_file_name = patient_hash + '.nrrd'  
        # Location of folder where nrrd file saved
        nrrd_folder_path = target_path + '/nrrd/'
        # Location of folder where pyradiomics output saved
        csv_path = target_path + '/CSV/'

    # Complete path of converted file
    nrrd_file_path = nrrd_folder_path + \
        nrrd_file_name  

    # If folder does not exist
    if not os.path.exists(nrrd_folder_path):  
        # Create folder
        os.makedirs(nrrd_folder_path)  

    convert_to_nrrd(path, nrrd_file_path)
    print('DICOM to nrrd completed')

    # Location of folder where converted masks saved
    mask_folder_path = nrrd_folder_path + \
        'structures'  
    convert_rois_to_nrrd(path, rtss_path, mask_folder_path)
    print('Segmentation masks converted')

    # Something went wrong, in this case PyRadiomics will also log an error
    if nrrd_file_path is None or nrrd_folder_path is None:
        print('Error getting testcase!')
        exit()

    radiomics_df = get_radiomics_df(
        path, patient_hash, nrrd_file_path, mask_folder_path)
    convert_df_to_csv(radiomics_df, patient_hash, csv_path)

    print('\n' + 'Pyradiomics csv generated.')

# For test purposes
# if __name__ == '__main__':
#     path = *file_path*
#     d, p = get_datasets(path)
#     pyradiomics(path, p)
