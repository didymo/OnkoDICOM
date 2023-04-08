import os
import pandas as pd
import platform
from radiomics import featureextractor


def convert_to_nrrd(path, nrrd_output_path):
    """
    Convert dicom files to nrrd.
    :param path: Path to patient directory (str)
    :param nrrd_file_path: Path to nrrd folder (str)
    """
    path = '"' + path + '"'
    nrrd_file_path = '"' + nrrd_output_path + '"'

    # Command to convert dicom files to nrrd
    # Writes the result from the processing into a temporary file
    # rather than the terminal
    cmd_for_nrrd = 'plastimatch convert --input ' + path + \
                   ' --output-img ' + nrrd_file_path + ' 1>' + path + '/NUL'

    # Command to delete the temporary file generated before
    cmd_del_nul = 'rm ' + path[:-1] + '/NUL' + '"'

    os.system(cmd_for_nrrd)

    if os.path.exists(path[1:-1] + '/NUL'):
        if platform.system() != "Windows":
            os.system(cmd_del_nul)
        else:
            cmd_del_nul = 'del ' + path[:-1] + '/NUL' + '"'
            os.system(cmd_del_nul)


def convert_rois_to_nrrd(path, rtss_path, mask_folder_path):
    """
    Generate an nrrd file for each region of interest using Plastimatch.
    :param path:                Path to patient directory (str)
    :param rtss_path:           Path to RT-Struct file (str)
    :param mask_folder_path:    Folder to which the segmentation masks
                                will be saved(str)
    """
    path = '"' + path + '"'
    mask_folder_path = '"' + mask_folder_path + '"'
    rtss_path = '"' + rtss_path + '"'
    # Command for generating an nrrd file for each region of interest
    cmd_for_segmask = 'plastimatch convert --input ' + rtss_path + \
        ' --output-prefix ' + mask_folder_path + \
        ' --prefix-format nrrd --referenced-ct ' + path + ' 1>' + \
        path + '/NUL'
    cmd_del_nul = 'rm ' + path[:-1] + '/NUL' + '"'
    os.system(cmd_for_segmask)

    if os.path.exists(path[1:-1] + '/NUL'):
        if platform.system() != "Windows":
            os.system(cmd_del_nul)
        else:
            cmd_del_nul = 'del ' + path[:-1] + '/NUL' + '"'
            os.system(cmd_del_nul)


def get_radiomics_df(path, patient_hash, nrrd_file_path, mask_folder_path):
    """
    Run pyradiomics and return pandas dataframe with all the computed data.
    :param path: Path to patient directory (str).
    :param patient_hash: Patient hash ID generated from their
                         identifiers.
    :param nrrd_file_path: Path to folder with converted nrrd file.
    :param mask_folder_path: Path to ROI nrrd files.
    :return: Pandas dataframe.
    """

    # Initialize feature extractor using default pyradiomics settings
    extractor = featureextractor.RadiomicsFeatureExtractor()

    # Contains the features for all the ROI
    all_features = []
    # CSV headers
    radiomics_headers = []
    feature_vector = ''

    # If RTSS selected has no ROIS
    if not os.listdir(mask_folder_path):
        return None

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


def clean_patient_id(patient_id):
    """
    Removes characters that cannot be used as part of file names.
    :param patient_id: patients ID
    return: cleaned up patient_id
    """
    invalid_characters = r'/\:*?"<>|'

    filename = ''

    for c in patient_id:
        if c not in invalid_characters:
            filename += c

    return filename


def convert_df_to_csv(radiomics_df, csv_path, patient_hash):
    """
    Export dataframe as a csv file.
    :param radiomics_df: dataframe containing radiomics data.
    :param csv_path: output folder path.
    :param patient_hash: patient's hash
    """

    # If folder does not exist
    if not os.path.exists(csv_path):
        # Create folder
        os.makedirs(csv_path)

    target_path = csv_path + 'Pyradiomics_' + patient_hash + '.csv'

    create_header = not os.path.isfile(target_path)

    # Export dataframe as csv
    radiomics_df.to_csv(target_path, header=create_header)
