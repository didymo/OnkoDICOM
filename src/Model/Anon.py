


#### THE Anonimization function for the patient identifiers #########
 
import os
import pydicom
import uuid
import csv
import pandas as pd


#========================================ANONYMIZation code ===================================


# CHECK if the identifiers exist in dicom file
def hasattribute(keyword, ds):
    return keyword in ds



## ===================================HASH Function================================================

def Hash_identifiers(file_no, ds_rtss):

    # ------------------------------------Sha1 hash for patient name-------------------------------------

    if 'PatientName' in ds_rtss:
        patient_name = str(ds_rtss.PatientName)
        # print("Patient name - ", patient_name)
        # MD 5 hashing
        hash_patient_name_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, patient_name)
        # Hashing the MD5 hash again using SHA1
        hash_patient_name_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_patient_name_MD5))
        # storing the hash to dataset
        ds_rtss.PatientName = str(hash_patient_name_sha1)
    else:
        print("NO patient Name found")

    # -----------------------------------------sha1 hash for patient ID------------------------------

    # if 'PatientID' in ds_rtss:
    if hasattribute("PatientID", ds_rtss):
        patient_ID = str(ds_rtss.PatientID)
        # print("Patient ID - ", patient_ID)
        # MD 5 hashing
        hash_patient_ID_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, patient_ID)
        # Hashing the MD5 hash again using SHA1
        hash_patient_ID_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_patient_ID_MD5))
        # storing the hash to dataset
        ds_rtss.PatientID = str(hash_patient_ID_sha1)
    else:
        print("NO patient ID not found")

    # #  storing patient_name and ID in one variable
    # if hasattribute("PatientID", ds_rtss):
    #     P_name_ID = patient_name + " + " + patient_ID
    # else:
    #     P_name_ID = patient_name + " + " + "PID_empty"

    # ----------------------------------------------sha1 hash for patient DOB---------------------------------------

    if 'PatientBirthDate' in ds_rtss:
        patient_DOB = str(ds_rtss.PatientBirthDate)
        # print("Patient DOB - ", patient_DOB)
        # MD 5 hashing
        hash_patient_DOB_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, patient_DOB)
        # Hashing the MD5 hash again using SHA1
        hash_patient_DOB_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_patient_DOB_MD5))
        # storing the hash to dataset
        ds_rtss.PatientBirthDate = str(hash_patient_DOB_sha1)
    else:
        print("Patient BirthDate not found")

    # --------------------------------------------sha1 hash for patient Sex------------------------------------

    if 'PatientSex' in ds_rtss:
        patient_sex = str(ds_rtss.PatientSex)
        # print("Patient Sex - ", patient_sex)
        # MD 5 hashing
        hash_patient_Sex_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, patient_sex)
        # Hashing the MD5 hash again using SHA1
        hash_patient_Sex_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_patient_Sex_MD5))
        # storing the hash to dataset
        ds_rtss.PatientSex = str(hash_patient_Sex_sha1)
    else:
        print("Patient Sex not found")


     # used to reture flag = 1 to indicate the first file is used for saving the hash in 
     # hash_CSV file so CSV function will not be performed for rest of the files.   
    if file_no == 1:
        if hasattribute("PatientID", ds_rtss):
            P_name_ID = patient_name + " + " + patient_ID
            print("Pname and ID=   ", P_name_ID)
        else:
            P_name_ID = patient_name + " + " + "PID_empty"
            print("Pname and ID=   ", P_name_ID)
        return (P_name_ID, hash_patient_name_sha1,1)
    else:
        return(0,hash_patient_name_sha1,0)



 ## ===================================CHECK FILE EXIST================================================

def checkFileExist(fileName):
    print("file name:-- ", fileName)  # printing file name

    if (fileName == "Hash_map.csv"):
        cwd = os.getcwd()  # getting the current working directory
        file_path = cwd + "/" + fileName  # concatenating the current working directory with the csv filename
        print("Full path :  ===========", file_path)  # print the full csv file path
        print("file exist: ", os.path.isfile(file_path))  # check if the file exist in the folder
        if (os.path.isfile(file_path)) == True:  # if file exist return True
            print("returning true-----------------------")
            return True
        else:
            print("returning false----------------------")  # if file not exist return false
            return False


 ## ===================================CTEATE CSV FILE================================================

def create_hash_csv(pname, sha1_pname, csv_filename):

    # print("Csv file name is : ",csv_filename)
    # csv_filename = str("Hash_map") + ".csv"
    if (checkFileExist(csv_filename)) == False:
        print("-----Creating CSV------")

        csv_header = []
        csv_header.append('Pname and ID')
        csv_header.append('Hashed_Pname')
        print("the headers are:--", csv_header)

        # hash_dictionary =  {patient_ID : hash_patient_ID}
        # print("dictionary values",hash_dictionary)

        df_identifier_csv = pd.DataFrame(columns=csv_header).round(2)
        df_identifier_csv.to_csv(csv_filename, index=False) # creating the CVS

        row = [pname, sha1_pname]
        with open(csv_filename, 'a') as csvFile:  # inserting the hash values
            writer = csv.writer(csvFile)
            writer.writerow(row)
            csvFile.close()

        # print("The dataframe",df_identifier_csv)
        print("---------CSV created-----------")
        # options()

    else:
        print("updating csv")
        row = [pname, sha1_pname]
        with open(csv_filename, 'a') as csvFile: # updating the CVS with hash values
            writer = csv.writer(csvFile)
            writer.writerow(row)
            csvFile.close()
        print("------CSV updated -----")

#====================== getting Modality and Instance_number for new dicom file name=========
def get_modality_ins_num(ds):

    modality = ds.Modality
    if modality == "RTSTRUCT" or (modality == "RTPLAN"):
        return modality,0
    else:
        Inum = str(ds.InstanceNumber)
        return modality,Inum


# ===================================Writing the hashed identifiers to DICOM FILE================================================
def write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_P_name):

    
    modality, Inum = get_modality_ins_num(ds_rtss)  
    
    # writing the New hashed dicom file with new name "Modality_Instance-Number_Hashed.dcm"
    if (modality == "RTSTRUCT"):
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = Dicom_folder_path + "/" + modality + "_" + "Hashed" +  ".dcm"
        print("File name prefix with (Hashed) ",full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    elif (modality == "RTPLAN"):
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = Dicom_folder_path + "/" + modality + "_" + "Hashed" +  ".dcm"
        print("File name prefix with (Hashed) ",full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    else:
         # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = Dicom_folder_path + "/" + modality + "_" + str(Inum) + "_" + "Hashed" +  ".dcm"
        print("File name prefix with (Hashed) ",full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")

# ===============================getting all file names================

def get_All_files(Dicom_folder_path):

    All_dcm_fileNames = os.listdir(Dicom_folder_path)
    print("ALL files: in fuction")
    return All_dcm_fileNames

# ## ===================================PRINTING THE HASH VALUES================================================

def Print_identifiers(ds_rtss):
    print("INSIDE PRINT================")
    print("Patient name in dataset not hash: ", ds_rtss.PatientName)
    print("Patient ID in dataset not hash: ", ds_rtss.PatientID)
    print("Patient DOB in dataset not hash: ", ds_rtss.PatientBirthDate)
    print("Patient SEX in dataset not hash: ", ds_rtss.PatientSex)
    print("\n\n")


# loading the dicom file 
def LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key):
    # Dicom_folder_path = self.path  # Getting and storing the Folder path of rtss.dcm file
    print("\n\nIn Load_DCM function: PATH of the dicom file is:-----", Dicom_folder_path)

    # concatinating the folder path and the filename
    Full_dicom_filepath = (Dicom_folder_path + "/" + Dicom_filename)
    print("In Load_DCM function: FULL PATH of dicom file is:----", Full_dicom_filepath)
    # ds_rtss = pydicom.dcmread(Full_dicom_filepath)
    ds_rtss = new_dict_dataset[key]
    print("In Load DCM function:",Dicom_filename,"loaded in ds_rtss")
    return ds_rtss

# ====================== Function to check if the file is sub-directory ==========   

def Check_if_folder(file_path):
    # store the boolean value after checking the type of file
    file_type = os.path.isdir(file_path)
    if file_type == True: # if the file is subdiirectory return true
        return True
    else:
        return False  # if not a subdirectory return False    

# ==============Check in patient identifiers are already hashed===========

def check_file_hashed(file_name, new_dict_dataset, key):
    if ("Hashed" in file_name):
        hash_value = new_dict_dataset[key].PatientName
        return True,hash_value
    else:
        return False,0

# ##==========================================Anon Function==========================================
def anon_call(path, new_dict_dataset, all_filepaths):
    
    print("\n\n====Anon Called====")
    Dicom_folder_path = path

    # All_dcm = get_All_files(Dicom_folder_path)
    # print("ALL files: in main \n\n")

    # count = 0 
    # for eachFile in All_dcm:
    #     count += 1


    count = 0
    for key in new_dict_dataset:
        count +=1

        # store the name of each dcm file in a variable
        Dicom_filename = os.path.basename(all_filepaths[key])     
        print("\n\nHASHING FILE ::::::=== ",Dicom_filename)

        # ds_rtss = new_dict_dataset[key]

        # print("\nMOdality is:   ", ds_rtss.Modality)
        # print("\nInstance Number is:   ", ds_rtss.InstanceNumber)

        # concatinating the folder path and the filename
        Full_dicom_filepath = (Dicom_folder_path + "/" + Dicom_filename)

        
        file_type = Check_if_folder(Full_dicom_filepath)

        if file_type != True:

            print("The file {} is Directory {}".format(Dicom_filename,file_type))

            Is_hashed, hash_value = check_file_hashed(Dicom_filename, new_dict_dataset, key) 

            

            if Is_hashed != True:

                print("Is hashed: {} and the hash_value is: {}".format(Is_hashed, hash_value))
                # loading the dicom file content into the dataframe.
                ds_rtss= LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key)
                print("\n\nloaded in ds_rtss:============ ", Dicom_filename)

                # calling the HASH function and it returns the (Pname + PID), (hashvalue) and
                # (flag = 1  will be used to restrict only one hash value per patient in the CSV file)
                pname_ID, sha1_pname, flag = Hash_identifiers(count, ds_rtss)
                print(" In main Pname and ID=  {} and SHA1_name: {}".format(pname_ID, sha1_pname))

                if flag == 1:   #(flag = 1 that will be used to restrict only one hash per patient in the CSV file)
                    print("\n\nFLAG --1111111111111111111111111")
                    print(" In main Pname and ID=  {} and SHA1_name: {}".format(pname_ID, sha1_pname))

                    Print_identifiers(ds_rtss)  # calling the print to show the identifiers
                    csv_filename = str("Hash_map") + ".csv"
                    # calling create CSV to store the the hashed value
                    create_hash_csv(pname_ID, sha1_pname, csv_filename) 
                    print("Calling WRITE FUNCTION when Csv called")
                    # write_hash_dcm(sha1_pname, Dicom_filename)
                    write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname)
                else:
                    print("\n\nFLAG --0000000000000000000000000")
                    print("CSV function not called")
                    print("Calling WRITE FUNCTION when Csv not called")
                    # write_hash_dcm(sha1_pname, Dicom_filename)
                    write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname)
            else:
                print("Is hashed: {} and the hash_value is: {}".format(Is_hashed, hash_value))
                print("Patient Identifiers already hashed")
                print("Just overwriting the files without hashing")
                ds_rtss= LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key)
                write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, hash_value)
                count = 0
                 
        else:
            print("\n\n\n======File {} is a Folder=====".format(Dicom_filename))    #     write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname)
            print("\n\n\n")  
    print("Total files hashed======", count)


def anonymize(path, Datasets, FilePaths):

    all_filepaths = FilePaths
    new_dict_dataset = Datasets
    print("\n\nCurrent Work Directory is:  ==== ",os.getcwd())
    print("IN ANON===================")
    print("\n\n\n=====Path in ANONYMIZation   ===",path)
    # print("=====Datasets========= in ANONYMIZation   ===",Datasets)
    print("\n\n\n=====FilePaths in ANONYMIZation   ===",all_filepaths)
    # print("The value for CT 0 is : ", new_dict_dataset[0])
    # for key in Datasets:
    #     if (key != 'rtplan' and key != 'rtss' and key != 'rtdose'):
    #         print("Values are:  ",Datasets[key])
    anon_call(path, new_dict_dataset, all_filepaths)


