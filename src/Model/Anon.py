#### THE Anonymization function for the patient identifiers #########

import csv
import logging
import os
import pathlib
import shutil
import uuid

import pandas as pd
import pydicom

from src.Model.CalculateDVHs import dvh2csv

# ========================================Anonymization code ===================================


## ===================================HASH Function================================================
def _gen_md5_and_sha1_hash(input):
    """generate a digest by generating a SHA1 digest and then applying an MD5 hash to the SHA1
    digest 

    Parameters
    ----------
    input : ``str``
        the plaintext information to be "anonymised"

    Return
    ------
    digest: ``str``
    """
    hashed_input = uuid.uuid5(uuid.NAMESPACE_URL, str(input))
    digest = uuid.uuid3(uuid.NAMESPACE_URL, str(hashed_input))
    return str(digest)


def _trim_bracketing_single_quotes(repval_string):
    length = len(repval_string)
    left_trim = repval_string

    if repval_string[0] == "'":
        left_trim = repval_string[1:]
        length -= 1
    right_trim = left_trim
    if left_trim[length - 1] == "'":
        right_trim = left_trim[: length - 1]
    return right_trim


def _create_reidentification_item(dicom_object_as_dataset):
    """Construct a re-identification key/value pair
    where the key is a concatenation of the patient name and the patient id with the + symbol
    e.g. "Jones^David^Xavier + ABC123" 
    and the value is the hash of the patient name (e.g. hash of Jones^David^Xavier)
    The string values do not include quotes.

    Parameters
    ----------
    dicom_object_as_dataset : ``pydicom.dataset.Dataset``
        A DICOM information object that contains a PatientName and a PatientID

    Returns
    -------
    ``string, string``
        PatientName + PatientID, anonymised_patient_name
    """
    patient_name = _trim_bracketing_single_quotes(
        dicom_object_as_dataset["PatientName"].repval
    )
    patient_ID = _trim_bracketing_single_quotes(
        dicom_object_as_dataset["PatientID"].repval
    )
    concatenated_identifier = f"{patient_name} + {patient_ID}"
    hash_patient_name = _gen_md5_and_sha1_hash(patient_name)
    return concatenated_identifier, hash_patient_name


def _hash_identifiers_in_place(ds_rtss):
    """in place anonymisation of a set of identifiers in a dataset
    Parameters
    ----------
    ds_rtss: ``pydicom.dataset.Dataset``
        A dataset to be anonymised

    Returns
    -------
    """
    mandatory_identifying_keys = [
        "PatientName",
        "PatientID",
    ]

    identifying_keys = [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientSex",
        "InstanceCreationDate",
        "StudyDate",
        "ContentDate",
        "StructureSetDate",
    ]

    for identifying_key in identifying_keys:
        try:
            if identifying_key in ds_rtss:
                identifier = _trim_bracketing_single_quotes(
                    ds_rtss[identifying_key].repval
                )
                hashed_identifier = _gen_md5_and_sha1_hash(identifier)
                ds_rtss[identifying_key].value = hashed_identifier
            else:
                logging_level = logging.INFO
                if identifying_key in mandatory_identifying_keys:
                    logging_level = logging.ERROR

                logging.log(
                    logging_level,
                    "%s not found in DICOM SOP Instance: %s",
                    identifying_key,
                    _trim_bracketing_single_quotes(ds_rtss["SOPInstanceUID"].repval),
                )
        except TypeError as e:
            print(identifying_key, " resulted in ", e)
            logging.error("%s identifying key resulted in %s", identifying_key, e)
            pass


def _check_identity_mapping_file_exists(fileName):
    """
    Determine if the unqualified name specified has a corresponding file
    in a partially qualified path relative to the current working directory.

    Parameters
    ----------
    fileName: ``str``
    The unqualified name of the desired or already available CSV file.
    However, if the file name provided is not patientHash.csv, the file is
    treated as if it doesn't exist (no actual check takes place).
    If the file name is patientHash.csv, then the partially qualified
    path src/data/csv/patientHash.csv relative to the current working directory
    will be utilised.

    Returns
    -------
    file_is_present: ``bool``
    fully qualified path: ``str``
        optionally returned, only if parameter had value "patientHash.csv"
    """
    print("file name:-- ", fileName)  # printing file name

    if fileName == "patientHash.csv":
        data_folder_path = "/src/data/csv/"
        cwd = os.getcwd()  # getting the current working directory
        file_path = (
            cwd + data_folder_path + fileName
        )  # concatenating the current working directory with the csv filename
        print("Full path :  ===========", file_path)  # print the full csv file path
        print(
            "file exist: ", os.path.isfile(file_path)
        )  # check if the file exist in the folder
        if (os.path.isfile(file_path)) == True:  # if file exist return True
            print("returning true-----------------------")
            return True, file_path
        else:
            print(
                "returning false----------------------"
            )  # if file not exist return false
            return False, file_path


def _create_reidentification_spreadsheet(pname, sha1_pname, csv_filename):
    """ Creates or appends a csv file whose rows contain
    the original patient identifer and the anonymised identifier

    Parameters
    ----------
    pname: ``str``
            The original patient identifer

    sha1_pname: ``str``
            The anonymised identifier

    csv_filename: ``str``
            The unqualified name of the desired or already available CSV file.
            However, if the file name provided is not patientHash.csv, the file will be 
            overwritten.  If the file name is patientHash.csv, then the partially qualified
            path src/data/csv/patientHash.csv relative to the current working directory
            will be utilised.  If the partially qualified path does not already exists,
            an error is raised.

    Returns
    -------
      
    """
    # print("Csv file name is : ",csv_filename)
    # chcek if the patientHash.csv exist
    Csv_Exist, csv_filePath = _check_identity_mapping_file_exists(csv_filename)

    # if the csv doent exist create a new CSV and export the Hash to that.
    if Csv_Exist == False:
        print("-----Creating CSV------")

        csv_header = []
        csv_header.append("Pname and ID")
        csv_header.append("Hashed_Pname")
        print("the headers are:--", csv_header)

        # hash_dictionary =  {patient_ID : hash_patient_ID}
        # print("dictionary values",hash_dictionary)

        row = [pname, sha1_pname]
        sheet = []
        sheet.append(row)
        df_identifier_csv = pd.DataFrame(columns=csv_header).round(2)

        print("The CSV dataframe is:::", df_identifier_csv)
        print("---")
        print(csv_filePath)
        df_identifier_csv.to_csv(csv_filePath, index=False)  # creating the CVS

        with open(csv_filePath, "a") as csvFile:  # inserting the hash values
            writer = csv.writer(csvFile)
            writer.writerow(row)
            csvFile.close()

        # print("The dataframe",df_identifier_csv)
        print("---------CSV created-----------")
        # options()

    else:
        print("updating csv")
        row = [pname, sha1_pname]
        with open(csv_filePath, "a") as csvFile:  # updating the CVS with hash values
            writer = csv.writer(csvFile)
            writer.writerow(row)
            csvFile.close()
        print("------CSV updated -----")


# ====================== getting Modality and Instance_number for new dicom file name=========
def _get_modality_ins_num(ds):

    modality = ds.Modality
    if modality == "RTSTRUCT" or (modality == "RTPLAN"):
        return modality, 0
    else:
        Inum = str(ds.InstanceNumber)
        return modality, Inum


# ===================================Writing the hashed identifiers to DICOM FILE================================================
def _write_hash_dcm(
    ds_rtss, Dicom_folder_path, Dicom_filename, sha1_P_name, new_patient_folder_name
):

    modality, Inum = _get_modality_ins_num(ds_rtss)

    SecondLastDir = os.path.dirname(
        Dicom_folder_path
    )  # getting path till the second last Folder

    # writing the New hashed dicom file with new name "Modality_Instance-Number_Hashed.dcm"
    if modality == "RTSTRUCT":
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = (
            SecondLastDir
            + "/"
            + new_patient_folder_name
            + "/"
            + modality
            + "_"
            + "Hashed"
            + ".dcm"
        )
        print("File name prefix with (Hashed) ", full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    elif modality == "RTPLAN":
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = (
            SecondLastDir
            + "/"
            + new_patient_folder_name
            + "/"
            + modality
            + "_"
            + "Hashed"
            + ".dcm"
        )
        print("File name prefix with (Hashed) ", full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    else:
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = (
            SecondLastDir
            + "/"
            + new_patient_folder_name
            + "/"
            + modality
            + "_"
            + str(Inum)
            + "_"
            + "Hashed"
            + ".dcm"
        )
        print("File name prefix with (Hashed) ", full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")


# ## ===================================PRINTING THE HASH VALUES================================================


def _print_patient_identifiers(ds_rtss):
    print("Patient name: ", ds_rtss.PatientName)
    print("Patient ID  : ", ds_rtss.PatientID)
    print("Patient DOB : ", ds_rtss.PatientBirthDate)
    print("Patient SEX : ", ds_rtss.PatientSex)
    print("\n\n")


def _is_directory(file_path):
    return os.path.isdir(file_path)


# ==============Check in patient identifiers are already hashed===========


def _check_file_hashed(file_name, new_dict_dataset, key, matching_text):
    """Returns whether the file_name contains the matching text
    and the PatientName in the dataset pointed to by the key in the dict of datasets

    Parameters
    ----------
    file_name: ``str``
        the name of the DICOM file

    new_dict_dataset: ``dict`` with key of type ``str``|``int``, value of type pydicom.dataset.Dataset
        dict of the Patient's DICOM data objects

    key: ``str``|``int``
        key in to new_dict_dataset identifying which dataset to use for finding the 
        PatientsName which is presumed to be Hashed
    
    matching_text: ``str``
        the text that indicates whether the file contains hashed data or not based on
    the assumption that the filename will contain the text if it contains hashed data.

    Returns
    -------
    is_hashed, hashed_patient_name: ``bool``, ``str``
        True when matching_text in file_name, PatientName presumed to be hashed or empty string
    """
    if matching_text in file_name:
        hash_value = new_dict_dataset[key].PatientName
        return True, hash_value
    else:
        return False, ""


def _create_anonymised_patient_folder(new_patient_folder_name, Dicom_folder_path):
    """Create the folder in which the anonymised patient's data will be placed

    Parameters
    ----------
    new_patient_folder_name : ``str``
        the unqualified path of the anonymised patient
    Dicom_folder_path : ``str``
        the fully or partially (relative to cwd) qualified path to the current patient's data
    """
    # getting the current working directory
    # Dicom_file_dir = os.getcwd()
    # Dicom_folder_path = self.path
    SecondLastDir = os.path.dirname(
        Dicom_folder_path
    )  # getting path till the second last Folder
    # concatinating the full path of the folder to store hashed files
    Full_Path_Patient_folder_new = SecondLastDir + "/" + new_patient_folder_name
    print("Full path patient new folder======", Full_Path_Patient_folder_new)

    # creating the new folder
    os.makedirs(
        Full_Path_Patient_folder_new
    )  # creating the new folder for New hashed files

    print("==================NEW FOLDER CREATED=========", Full_Path_Patient_folder_new)
    print("\n\n")
    # src_files = os.listdir(source_path)


# ========================CHECK if hashed FOLDER exist=======================================


def _build_anonymisation_folder_name(
    dicom_object_as_dataset, patient_folder_path, file_previously_hashed
):
    """Provide partially or fully qualified path to where the anonymisation data should go

    Parameters
    ----------
    dicom_object_as_dataset : ``pydicom.dataset.Dataset``
        Any one of the DICOM objects for the patient, but specifically the one where the 
        patient name is considered to be correct and complete
    patient_folder_path : ``str``
        the partially or fully qualified path from which the hierarchy of files for the patient
        were read.  
    file_previously_hashed : ``bool``
        Whether the data in hand should be assumed to have had the identifiers already anonymised

    Returns
    -------
    ``str|path``
        A Path-like object that specifies where the anonymised data is to be written
    """
    patient_name = _trim_bracketing_single_quotes(
        dicom_object_as_dataset["PatientName"].repval
    )
    if file_previously_hashed:
        hashed_patient_name = patient_name  # it's already been hashed
    else:
        hashed_patient_name = _gen_md5_and_sha1_hash(patient_name)

    grandparent_folder = os.path.dirname(patient_folder_path)
    anonymisation_folder = pathlib.Path().joinpath(
        grandparent_folder, hashed_patient_name
    )

    return anonymisation_folder


def _anonymisation_folder_exists(
    new_dict_dataset, all_filepaths, Dicom_folder_path, File_hash_status
):

    """check if the directory of the hashed patient's name exists in the specified folder
    current implementation uses a hash of the PatientName for the name of the folder
    in which to place all of the patient's anonymised data, parallel to the directory
    containing the original not anonymised patient data.

    Parameters
    ----------
    new_dict_dataset: ``dict`` where values are ``pydicom.dataset.Dataset``
        dictionary of the DICOM data objects for the patient

    all_filepaths: ``list`` of str
        list of the paths to the files containing the DICOM objects in new_dict_dataset
    
    Dicom_folder_path:  ``str``
        the directory containing the current patient's DICOM data
    
    File_hash_status: ``int`` 
        representing a boolean indicating whether the datasets in new_dict_dataset
        have already been anonymised. 0 is False.

    Return
    ------
        directory_exists: ``int`` as boolean 

        anonymisation_folder_name:  ``str``
            unqualified path, hashed patient name

        fully_qualified_anonymisation_folder_name: ``str``

    """

    first_file = os.path.basename(all_filepaths[0])
    # print("THE PATH IN THE CHECK FOLDER::::::::::", all_filepaths[0] )
    if File_hash_status == 0:

        # ds_rtss = LOAD_DCM(Dicom_folder_path, first_file, new_dict_dataset, 0)
        ds_rtss = new_dict_dataset[0]
        # if the PatientName isn't found, all kinds of problems will ensue
        # just let Python raise the error
        hash_patient_name_sha1_first = _gen_md5_and_sha1_hash(
            _trim_bracketing_single_quotes(ds_rtss["PatientName"].repval)
        )

        _print_patient_identifiers(ds_rtss)

        new_patient_folder_name = hash_patient_name_sha1_first
        print("New patient folder==", new_patient_folder_name)

        SecondLastDir = os.path.dirname(
            Dicom_folder_path
        )  # getting path till the second last Folder

        Full_Patient_Path_New_folder = SecondLastDir + "/" + new_patient_folder_name

        # check if the hashed Folder name exist in the Specified folder
        if new_patient_folder_name in os.listdir(SecondLastDir):
            return 1, new_patient_folder_name, Full_Patient_Path_New_folder
        else:
            return 0, new_patient_folder_name, Full_Patient_Path_New_folder
    else:
        SecondLastDir = os.path.dirname(
            Dicom_folder_path
        )  # getting path till the second last Folder

        # ds_rtss = LOAD_DCM(Dicom_folder_path, first_file, new_dict_dataset, 0)
        ds_rtss = new_dict_dataset[0]
        new_patient_folder_name = str(ds_rtss.PatientName)

        Full_Patient_Path_New_folder = SecondLastDir + "/" + new_patient_folder_name

        # check if the hashed Folder name exist in the Specified folder
        if new_patient_folder_name in os.listdir(SecondLastDir):
            return 1, new_patient_folder_name, Full_Patient_Path_New_folder
        else:
            return 0, new_patient_folder_name, Full_Patient_Path_New_folder


def _anonymise_dicom_data(path, new_dict_dataset, all_filepaths):
    """create anonymised copies of DICOM data that are specified in a list of paths
    Parameters
    ----------
    path: ``str``
        The top level directory in which to create a subdirectory for the anonymised data

    new_dict_dataset: ``dict`` 
        keys are of type ``str`` and either DICOM Object type identifiers or integer value of count of 
        volumetric image slices.
        values are pydicom.dataset.Dataset

    all_filepaths: list of ``str``
        the items in the list are paths to the individual DICOM objects

    Returns
    -------
    anonymised_data_dirname: ``str``
        path to the anonymised data directory, (subdirectory of path parameter)
    """
    logging.debug("entered _anonymise_dicom_data")
    Dicom_folder_path = path

    # There are a pair of binary choices that drive variation in action
    # 1)  Is the data in hand already anonymised
    #   (was it read in from files that were already anonymised using this tool)
    # 2)  Is there already a directory in place that indicates the patient had data
    #   anonymised previously (whether it's the same as the data in hand or something different)

    first_dicom_file = os.path.basename(all_filepaths[0])
    first_dicom_object = next(iter(new_dict_dataset.values()))
    text = "Hashed"
    (
        current_datasets_previously_anonymised,
        patient_name_in_dataset,
    ) = _check_file_hashed(first_dicom_file, new_dict_dataset, 0, text)

    if current_datasets_previously_anonymised:
        print(
            "Filename contains text: ",
            text,
            " assuming this data was already anonymised",
        )
    else:
        print(
            "Filename does not contain text: ",
            text,
            " assuming this data has not been anonymised",
        )

    Full_Patient_Path_New_folder = _build_anonymisation_folder_name(
        first_dicom_object, Dicom_folder_path, current_datasets_previously_anonymised
    )
    Exist_folder = os.path.exists(Full_Patient_Path_New_folder)
    new_patient_folder_name = os.path.basename(Full_Patient_Path_New_folder)

    if Exist_folder == 0:
        print("The folder for this patient's anonymised data does not exist")
        print(
            "Creating the new anonymised patient folder {} under {}".format(
                new_patient_folder_name, Dicom_folder_path
            )
        )
        _create_anonymised_patient_folder(
            new_patient_folder_name, Dicom_folder_path
        )  # calling create_folder function
        patient_had_previous_anonymisation = False
    else:
        patient_had_previous_anonymisation = True

    if not current_datasets_previously_anonymised:
        print(
            "Data currently loaded for this patient has not been anonymised: {}".format(
                patient_name_in_dataset
            )
        )
        first_dicom_object = next(iter(new_dict_dataset.values()))

        pname_ID, sha1_pname = _create_reidentification_item(first_dicom_object)
        print("First dataset for patient")
        _print_patient_identifiers(first_dicom_object)
        print("Patient name + ID=  {} and hashed name: {}".format(pname_ID, sha1_pname))
        if not patient_had_previous_anonymisation:
            # only one entry per patient in the CSV file
            # TODO: put the logic for unique entries down in the function
            #       that manipulates the spreadsheet/CSV.
            #   The current approach assumes that because there is an anonymised patient directory that there is an entry
            #   in the re-identification spreadsheet
            csv_filename = "patientHash.csv"
            # store the the original vs. hashed values
            # appends if the re-identification spreadsheet is already present
            _create_reidentification_spreadsheet(pname_ID, sha1_pname, csv_filename)
            print("Updating patient re-identification spreadsheet")

    count = 0

    for key, dicom_obj in new_dict_dataset.items():
        count += 1

        # store the name of each dcm file in a variable
        Dicom_filename = os.path.basename(all_filepaths[key])
        logging.debug("Operating on: %s", Dicom_filename)
        # concatenating the folder path and the filename
        Full_dicom_filepath = Dicom_folder_path + "/" + Dicom_filename

        path_is_directory = _is_directory(Full_dicom_filepath)

        if path_is_directory:
            print("\n\n\n======File {} is a Folder=====".format(Dicom_filename))
            print("\n\n\n")
            continue

        ds_rtss = dicom_obj
        print("\n\nloaded in ds_rtss:============ ", Dicom_filename)

        if not current_datasets_previously_anonymised:
            # calling the HASH function (anonymising)
            _hash_identifiers_in_place(ds_rtss)
        else:
            # the data in hand was already anonymised
            sha1_pname = patient_name_in_dataset

        logging.debug("Saving anonymised DICOM data")
        _write_hash_dcm(
            ds_rtss,
            Dicom_folder_path,
            Dicom_filename,
            sha1_pname,
            new_patient_folder_name,
        )

    logging.info("Saved %d files", count)
    if current_datasets_previously_anonymised:
        count = 0  # nothing was anonymised, just written to anonymisation folder as is
    print("Total files hashed======", count)
    return Full_Patient_Path_New_folder


def _file_previously_anonymised(file_path):
    """Determine if the file was previously anonymised, i.e.
    contains anonymised data.
    Used to avoid re-applying anonymisation algorithms to the identifiers
    The current algorithm simply searches for the text string "Hashed" in the basename

    Parameters
    ----------
    file_path : ``str`` | ``pathlib.Path``
        path to a DICOM file that is part of the patient's data

    Returns
    -------
    ``bool``
        True if the data appears to have been anonymised previously
    """
    return "Hashed" in os.path.basename(file_path)


def anonymize(path, Datasets, FilePaths, rawdvh):
    """
    Create an anonymised copy of an entire patient data set, including
    DICOM files,
    DHV CSV file,
    Clinical Data CSV file,
    Pyradiomics CSV file
    and place it in a subdirectory of the specified path

    Parameters
    ----------
    path: ``str``
        The current patient Directory.
        The anonymised data will be placed parallel to it, i.e. a child of the same parent directory

    Datasets: ``dict`` with values of ``pydicom.dataset.Dataset``
        The set of DICOM data for the patient to be anonymised

    Filepaths: ``list`` of ``string``
        The list of fully or partially qualified (relative to current working directory) filenames
        pointing to the patient's DICOM data

    rawdvh: ``dict`` with key = ROINumber, value = DVH 
        a representation of the Dose Volume Histogram 

    Returns
    -------
    Full_Patient_Path_New_folder: ``str``
        The fully qualified directory name where the anonymised data has been placed
    """

    all_filepaths = FilePaths
    new_dict_dataset = Datasets
    first_file_path = next(iter(all_filepaths.values()))
    first_dicom_object = next(iter(new_dict_dataset.values()))
    print("\n\nCurrent Work Directory is:  ==== ", os.getcwd())
    print("IN ANON===================")
    print("\n\n\n=====Path in ANONYMIZation   ===", path)
    # print("=====Datasets========= in ANONYMIZation   ===",Datasets)
    print("\n\n\n=====FilePaths in ANONYMIZation   ===")  # ), all_filepaths)
    for key, filepath in all_filepaths.items():
        print(key, ":", filepath)
    # print("The value for CT 0 is : ", new_dict_dataset[0])
    # for key in Datasets:
    #     if (key != 'rtplan' and key != 'rtss' and key != 'rtdose'):
    #         print("Values are:  ",Datasets[key])

    file_previously_anonymised = _file_previously_anonymised(first_file_path)

    Original_P_ID = first_dicom_object.PatientID

    patient_name_in_dataset = _trim_bracketing_single_quotes(
        first_dicom_object["PatientName"].repval
    )

    if not file_previously_anonymised:
        hashed_patient_id = _gen_md5_and_sha1_hash(Original_P_ID)
        hashed_patient_name = _gen_md5_and_sha1_hash(patient_name_in_dataset)
    else:
        hashed_patient_id = Original_P_ID
        hashed_patient_name = patient_name_in_dataset

    # this build up of the anonymisation folder is not needed yet
    # because _anon_call returns it, but I'd like to separate
    # the "anonymise the DICOM data" from "where does everything go"
    anonymised_patient_full_path = _build_anonymisation_folder_name(
        first_dicom_object, path, file_previously_anonymised
    )
    # _anon_call currently modifies the datasets in hand as part of anonymisation
    # if the data does not appear to have already been anonymised
    anonymised_patient_full_path = _anonymise_dicom_data(
        path, new_dict_dataset, all_filepaths
    )
    print("\n\nThe New patient folder path is : ", anonymised_patient_full_path)

    anonymisation_csv_full_path = pathlib.Path().joinpath(
        anonymised_patient_full_path, "CSV"
    )
    if not os.path.exists(anonymisation_csv_full_path):
        os.makedirs(anonymisation_csv_full_path)

    _export_anonymised_dvh_data(
        Original_P_ID, path, hashed_patient_id, anonymisation_csv_full_path
    )

    _export_anonymised_clinical_data(
        Original_P_ID, path, hashed_patient_id, anonymisation_csv_full_path
    )

    _export_anonymised_pyradiomics_data(
        Original_P_ID,
        path,
        hashed_patient_id,
        anonymisation_csv_full_path,
        export_nrrd_files=False,  # TODO: ask AAM if he wants the nrrd files themselves copied
    )

    return anonymised_patient_full_path


def _export_anonymised_clinical_data(
    current_patient_id,
    current_patient_top_directory,
    anonymised_patient_id,
    destination_csv_directory,
):
    """Reads in the previously stored spreadsheet/ CSV file, replaces the patient ID
    in the contents of the CSV, and writes it out with a filename using the anonymised 
    patient id to the anonymised patient directory tree.  If there are additional column
    updates, address those as well (note that column updates are "same value in each row")


    Parameters
    ----------
    current_patient_id : ``str``
        The PatientID as read in from the data for the current patient
    current_patient_top_directory : ``str`` | ``Path``
        The fully or partially qualified path to the top level directory of the current patient's data
    anonymised_patient_id : ``str``
        The anonymised patient ID
    destination_csv_directory : ``str`` | ``Path``
        Fully qualified path to the destination directory for the anonymised Clinical Data
    """
    _export_anonymised_spreadsheet_data(
        current_patient_id,
        current_patient_top_directory,
        anonymised_patient_id,
        destination_csv_directory,
        "ClinicalData",
        "PatientID",
    )


def _export_anonymised_pyradiomics_data(
    current_patient_id,
    current_patient_top_directory,
    anonymised_patient_id,
    destination_csv_directory,
    export_nrrd_files=False,
):
    """Reads in the previously stored spreadsheet/ CSV file, replaces the patient ID
    in the contents of the CSV, and writes it out with a filename using the anonymised 
    patient id to the anonymised patient directory tree.  If there are additional column
    updates, address those as well (note that column updates are "same value in each row")


    Parameters
    ----------
    current_patient_id : ``str``
        The PatientID as read in from the data for the current patient
    current_patient_top_directory : ``str`` | ``Path``
        The fully or partially qualified path to the top level directory of the current patient's data
    anonymised_patient_id : ``str``
        The anonymised patient ID
    destination_csv_directory : ``str`` | ``Path``
        Fully qualified path to the destination directory for the anonymised Clinical Data
    """
    directory_path_replacement = dict()
    directory_path_replacement["Directory Path"] = pathlib.Path(
        destination_csv_directory
    ).parent
    _export_anonymised_spreadsheet_data(
        current_patient_id,
        current_patient_top_directory,
        anonymised_patient_id,
        destination_csv_directory,
        "Pyradiomics",
        "Hash ID",
        additional_column_updates=directory_path_replacement,
    )
    if export_nrrd_files:
        print("copying across the raw nrrd files")

        _export_anonymised_nrrd_files(
            current_patient_top_directory,
            destination_csv_directory,
            current_patient_id,
            anonymised_patient_id,
        )

        print("finished exporting anonymised nrrd files")
    else:
        print("skipping the raw nrrd files")
    return


def _export_anonymised_nrrd_files(
    current_patient_top_directory,
    destination_csv_directory,
    current_patient_id,
    anonymised_patient_id,
):
    """Copies across the nrrd files, changing the name of the top level identifying nrrd file

    Parameters
    ----------
    current_patient_top_directory : ``str|Path``
        directory that contains the nrrd subdirectory
    destination_csv_directory : ``str|Path``
        the destination for CSV files, shares the parent with the destination nrrd directory
        TODO: replace this argument with the destination parent itself
    current_patient_id : ``str``
        patient id as found in the data currently loaded
    anonymised_patient_id : ``str``
        the anonymised patient id will be used to replace file name fragments
    """
    # print("in _export_anonymised_nrrd_files")
    current_nrrd_path = pathlib.Path().joinpath(current_patient_top_directory, "nrrd")
    print("Source: ", str(current_nrrd_path))
    if not os.path.exists(current_nrrd_path):
        logging.warning(
            "%s not present, there are no raw nrrd files to copy", current_nrrd_path
        )
        return
    # CSV and nrrd share the same parent directory
    destination_nrrd_parent_path = (
        pathlib.Path().joinpath(destination_csv_directory).parent
    )
    destination_nrrd_path = pathlib.Path().joinpath(
        destination_nrrd_parent_path, "nrrd"
    )
    print("Destination:", str(destination_nrrd_path))
    if os.path.exists(destination_nrrd_path):
        logging.warning(
            "%s is already present, skipping anonymisation of nrrd files",
            destination_nrrd_path,
        )
        return

    shutil.copytree(current_nrrd_path, destination_nrrd_path)

    # the identifying nrrd file from the current patient data
    # was copied verbatim, so we need to rename it.
    identifying_nrrd_filename = current_patient_id + ".nrrd"
    anonymised_nrrd_filename = anonymised_patient_id + ".nrrd"
    if current_patient_id != anonymised_patient_id:
        identifying_nrrd_full_path = pathlib.Path().joinpath(
            destination_nrrd_path, identifying_nrrd_filename
        )
        anonymised_nrrd_full_path = pathlib.Path().joinpath(
            destination_nrrd_path, anonymised_nrrd_filename
        )

        shutil.move(identifying_nrrd_full_path, anonymised_nrrd_full_path)


def _export_anonymised_spreadsheet_data(
    current_patient_id,
    current_patient_top_directory,
    anonymised_patient_id,
    destination_csv_directory,
    spreadsheet_type_name,
    patient_id_column_name,
    additional_column_updates=None,
):
    """Reads in the previously stored spreadsheet/ CSV file, replaces the patient ID
    in the contents of the CSV, and writes it out with a filename using the anonymised 
    patient id to the anonymised patient directory tree.  If there are additional column
    updates, address those as well (note that column updates are "same value in each row")


    Parameters
    ----------
    current_patient_id : ``str``
        The PatientID as read in from the data for the current patient
    current_patient_top_directory : ``str`` | ``Path``
        The fully or partially qualified path to the top level directory of the current patient's data
    anonymised_patient_id : ``str``
        The anonymised patient ID
    destination_csv_directory : ``str`` | ``Path``
        Fully qualified path to the destination directory for the anonymised Clinical Data
    spreadsheet_type_name: ``str``
        The first part of the name of the spreadsheet, e.g. ClinicalData or Pyradiomics
        which also describes the type of data to be found in the spreadsheet/CSV file.
    patient_id_column_name: ``str``
        Different spreadsheets unfortunately use different column names for the patient id.
        This provides flexibility in identifying which column is involved.
    additional_column_updates: ``dict`` of {column_name:``str``, update_value:``str``}
        If the spreadsheet has any additional columns containing some kind of identifying information.
        e.g. {"Directory Path":"/home/sweet/home",}
    """
    logging.debug("starting %s spreadsheet anonymisation", spreadsheet_type_name)

    spreadsheet_data_original_file_name = (
        spreadsheet_type_name + "_" + current_patient_id + ".csv"
    )
    logging.debug(
        "spreadsheet file name to check: %s", spreadsheet_data_original_file_name
    )

    spreadsheet_data_original_directory = pathlib.Path().joinpath(
        current_patient_top_directory, "CSV"
    )

    original_spreadsheet_data_full_file_path = spreadsheet_data_original_directory.joinpath(
        spreadsheet_data_original_file_name
    )
    print(
        "The full path of the spreadsheet file to check:",
        original_spreadsheet_data_full_file_path,
    )

    anonymised_spreadsheet_data_file_name = (
        spreadsheet_type_name + "_" + anonymised_patient_id + ".csv"
    )
    anonymised_spreadsheet_full_file_path = pathlib.Path().joinpath(
        destination_csv_directory, anonymised_spreadsheet_data_file_name
    )

    if not os.path.exists(destination_csv_directory):
        # new behaviour.  Make it rather than skip it.
        # this allows reordering of export tasks and avoids
        # relying on some other code to put the CSV directory in place
        os.makedirs(destination_csv_directory)

    if os.path.exists(original_spreadsheet_data_full_file_path):
        print("Updating the spreadsheet with the anonymised PatientID")

        spreadsheet_dataframe = pd.read_csv(original_spreadsheet_data_full_file_path)
        print("The  Dataframe is :::\n\n", spreadsheet_dataframe)

        column_name_list = list(spreadsheet_dataframe.columns)
        index_of_patient_id_column = 0
        try:
            index_of_patient_id_column = column_name_list.index(patient_id_column_name)

        except ValueError:
            logging.error(
                "Unable to find column %s in spreadsheet %s",
                patient_id_column_name,
                original_spreadsheet_data_full_file_path,
            )
            # probably time to return or raise error, but this wasn't being checked before
            pass

        P_count = spreadsheet_dataframe[patient_id_column_name].count()
        print("The count of PatientId is ::::", P_count)

        for i in range(0, P_count):
            # ClinicalData_DF[]
            # print(spreadsheet_dataframe.iloc[i, index_of_patient_id_column])
            # print("Changing the value in dataframe")
            spreadsheet_dataframe.iloc[
                i, index_of_patient_id_column
            ] = anonymised_patient_id

        if additional_column_updates is not None:
            for column_name, update_value in additional_column_updates.items():
                try:
                    index_of_column = column_name_list.index(column_name)
                    rows = spreadsheet_dataframe[column_name].count()
                    for i in range(0, rows):
                        spreadsheet_dataframe.iloc[i, index_of_column] = update_value
                except ValueError:
                    logging.error(
                        "%s column not found in %s",
                        column_name,
                        original_spreadsheet_data_full_file_path,
                    )

        print("The Dataframe after change is :::\n\n", spreadsheet_dataframe)
        # write out the updated information
        spreadsheet_dataframe.to_csv(anonymised_spreadsheet_full_file_path, index=False)
        logging.debug("%s spreadsheet anonymisation succeeded", spreadsheet_type_name)

    else:
        print(
            "The current patient dataset did not include a ",
            spreadsheet_type_name,
            " data file",
        )
        print("No ", spreadsheet_type_name, " file to anonymise")

    logging.debug("%s spreadsheet anonymisation finished", spreadsheet_type_name)


def _export_anonymised_dvh_data(
    current_patient_id,
    current_patient_top_directory,
    anonymised_patient_id,
    destination_csv_directory,
):
    """Reads in the previously stored spreadsheet/ CSV file, replaces the patient ID
    in the contents of the CSV, and writes it out with a filename using the anonymised 
    patient id to the anonymised patient directory tree.  If there are additional column
    updates, address those as well (note that column updates are "same value in each row")


    Parameters
    ----------
    current_patient_id : ``str``
        The PatientID as read in from the data for the current patient
    current_patient_top_directory : ``str`` | ``Path``
        The fully or partially qualified path to the top level directory of the current patient's data
    anonymised_patient_id : ``str``
        The anonymised patient ID
    destination_csv_directory : ``str`` | ``Path``
        Fully qualified path to the destination directory for the anonymised DVH Data
    """
    _export_anonymised_spreadsheet_data(
        current_patient_id,
        current_patient_top_directory,
        anonymised_patient_id,
        destination_csv_directory,
        "DVH",
        "Patient ID",
    )
