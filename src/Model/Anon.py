


#### THE Anonimization function for the patient identifiers #########
 
import os
import pydicom
import uuid
import csv
import pandas as pd
from src.Model.Pyradiomics import pyradiomics
from src.Model.CalculateDVHs import dvh2csv

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


    #----------instance creation------------

    if 'InstanceCreationDate' in ds_rtss:
        Instance_creation_Date= str(ds_rtss.InstanceCreationDate)
        # print("Patient Sex - ", patient_sex)
        # MD 5 hashing
        hash_Instance_creation_Date_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, Instance_creation_Date)
        # Hashing the MD5 hash again using SHA1
        hash_Instance_creation_Date_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_Instance_creation_Date_MD5))
        # storing the hash to dataset
        ds_rtss.InstanceCreationDate = str(hash_Instance_creation_Date_sha1)
    else:
        print("Instance Creation date not found")


    #-----------STUDY date--------------
    if 'StudyDate' in ds_rtss:
        Study_Date = str(ds_rtss.StudyDate)
        # print("Patient Sex - ", patient_sex)
        # MD 5 hashing
        hash_Study_Date_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, Study_Date)
        # Hashing the MD5 hash again using SHA1
        hash_Study_Date_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_Study_Date_MD5))
        # storing the hash to dataset
        ds_rtss.StudyDate = str(hash_Study_Date_sha1)
    else:
        print("Patient Study_Date not found")

    #-----------------content date date-----------
    if 'ContentDate' in ds_rtss:
        Content_Date = str(ds_rtss.ContentDate)
        # print("Patient Sex - ", patient_sex)
        # MD 5 hashing
        hash_Content_Date_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, Content_Date)
        # Hashing the MD5 hash again using SHA1
        hash_Content_Date_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_Content_Date_MD5))
        # storing the hash to dataset
        ds_rtss.ContentDate = str(hash_Content_Date_sha1)
    else:
        print("Patient Content_Date not found")    


    #------------------Structure set date-----------------

    if 'StructureSetDate' in ds_rtss:
        Structure_Set_Date = str(ds_rtss.StructureSetDate)
        # print("Patient Sex - ", patient_sex)
        # MD 5 hashing
        hash_Structure_Set_Date_MD5 = uuid.uuid5(uuid.NAMESPACE_URL, Structure_Set_Date)
        # Hashing the MD5 hash again using SHA1
        hash_Structure_Set_Date_sha1 = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_Structure_Set_Date_MD5))
        # storing the hash to dataset
        ds_rtss.StructureSetDate = str(hash_Structure_Set_Date_sha1)
    else:
        print("Patient Content_Date not found")  


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

    if (fileName == "patientHash.csv"):
        data_folder_path = "/src/data/csv/"
        cwd = os.getcwd()  # getting the current working directory
        file_path = cwd + data_folder_path + fileName  # concatenating the current working directory with the csv filename
        print("Full path :  ===========", file_path)  # print the full csv file path
        print("file exist: ", os.path.isfile(file_path))  # check if the file exist in the folder
        if (os.path.isfile(file_path)) == True:  # if file exist return True
            print("returning true-----------------------")
            return True, file_path
        else:
            print("returning false----------------------")  # if file not exist return false
            return False, file_path


 ## ===================================CTEATE CSV FILE================================================

def create_hash_csv(pname, sha1_pname, csv_filename):

    # print("Csv file name is : ",csv_filename)
    # chcek if the patientHash.csv exist
    Csv_Exist, csv_filePath = checkFileExist(csv_filename)

    # if the csv doent exist create a new CSV and export the Hash to that. 
    if (Csv_Exist == False):
        print("-----Creating CSV------")

        csv_header = []
        csv_header.append('Pname and ID')
        csv_header.append('Hashed_Pname')
        print("the headers are:--", csv_header)

        # hash_dictionary =  {patient_ID : hash_patient_ID}
        # print("dictionary values",hash_dictionary)
        
        df_identifier_csv = pd.DataFrame(columns=csv_header).round(2)

        print("The CSV dataframe is:::",df_identifier_csv)

        df_identifier_csv.to_csv(csv_filePath, index=False) # creating the CVS

        row = [pname, sha1_pname]
        with open(csv_filePath, 'a') as csvFile:  # inserting the hash values
            writer = csv.writer(csvFile)
            writer.writerow(row)
            csvFile.close()

        # print("The dataframe",df_identifier_csv)
        print("---------CSV created-----------")
        # options()

    else:
        print("updating csv")
        row = [pname, sha1_pname]
        with open(csv_filePath, 'a') as csvFile: # updating the CVS with hash values
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
def write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_P_name, new_patient_folder_name):

    
    modality, Inum = get_modality_ins_num(ds_rtss)  

    SecondLastDir = os.path.dirname(Dicom_folder_path) # getting path till the second last Folder

    # writing the New hashed dicom file with new name "Modality_Instance-Number_Hashed.dcm"
    if (modality == "RTSTRUCT"):
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = SecondLastDir + "/" + new_patient_folder_name  + "/" + modality + "_" + "Hashed" +  ".dcm"
        print("File name prefix with (Hashed) ",full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    elif (modality == "RTPLAN"):
        # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = SecondLastDir + "/" +  new_patient_folder_name + "/" + modality + "_" + "Hashed" +  ".dcm"
        print("File name prefix with (Hashed) ",full_path_new_file)

        ds_rtss.save_as(full_path_new_file)
        print(":::::::Write complete :::")
    else:
         # # Adding Prefix "Hashed " for each anonymized Dicom file and concat the file and folder
        full_path_new_file = SecondLastDir + "/" + new_patient_folder_name  + "/" + modality + "_" + str(Inum) + "_" + "Hashed" +  ".dcm"
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

def check_file_hashed(file_name, new_dict_dataset, key, text):
    if (text in file_name):
        hash_value = new_dict_dataset[key].PatientName
        return True,hash_value
    else:
        return False,0




# #######################   Create the NEw folder   #########################

def Create_New_Folder(new_patient_folder_name, Dicom_folder_path):

    
    # getting the current working directory
    # Dicom_file_dir = os.getcwd()
    # Dicom_folder_path = self.path
    SecondLastDir = os.path.dirname(Dicom_folder_path) # getting path till the second last Folder
    # concatinating the full path of the folder to store hashed files 
    Full_Path_Patient_folder_new = SecondLastDir + "/" + new_patient_folder_name
    print("Full path patient new folder======", Full_Path_Patient_folder_new)

    # creating the new folder
    os.makedirs(Full_Path_Patient_folder_new)  # creating the new folder for New hashed files

    print("==================NEW FOLDER CREATED=========",Full_Path_Patient_folder_new)
    print("\n\n")
    # src_files = os.listdir(source_path)



#========================CHECK if hashed FOLDER exist=======================================

def check_folder_exist(new_dict_dataset, all_filepaths, Dicom_folder_path , File_hash_status):

    first_file = os.path.basename(all_filepaths[0])
    # print("THE PATH IN THE CHECK FOLDER::::::::::", all_filepaths[0] )
    if File_hash_status == 0:
        
        ds_rtss= LOAD_DCM(Dicom_folder_path,first_file, new_dict_dataset, 0)

        if 'PatientName' in ds_rtss:
            patient_name_first = str(ds_rtss.PatientName)
            # MD 5 hashing
            hash_patient_name_MD5_first = uuid.uuid5(uuid.NAMESPACE_URL, patient_name_first)
            # Hashing the MD5 hash again using SHA1
            hash_patient_name_sha1_first = uuid.uuid3(uuid.NAMESPACE_URL, str(hash_patient_name_MD5_first))
            hash_patient_name_sha1_first = str(hash_patient_name_sha1_first)
        else:
            print("NO patient Name found")

        print("Original patient name = =======================================", str(ds_rtss.PatientName))   
        print("Original patient ID = =======================================", str(ds_rtss.PatientID))
        print("Original patient name = =======================================", str(ds_rtss.PatientBirthDate))
        print("Original patient name = =======================================", str(ds_rtss.PatientSex))

        new_patient_folder_name = hash_patient_name_sha1_first
        print("New patient folder==", new_patient_folder_name)

        SecondLastDir = os.path.dirname(Dicom_folder_path)  # getting path till the second last Folder

        Full_Patient_Path_New_folder  = SecondLastDir + "/" + new_patient_folder_name

        # check if the hashed Folder name exist in the Specified folder
        if new_patient_folder_name in os.listdir(SecondLastDir):
            return 1, new_patient_folder_name, Full_Patient_Path_New_folder
        else:
            return 0, new_patient_folder_name, Full_Patient_Path_New_folder 
    else:
        SecondLastDir = os.path.dirname(Dicom_folder_path)  # getting path till the second last Folder

        ds_rtss= LOAD_DCM(Dicom_folder_path,first_file, new_dict_dataset, 0)

        new_patient_folder_name = str(ds_rtss.PatientName)

        Full_Patient_Path_New_folder  = SecondLastDir + "/" + new_patient_folder_name

        # check if the hashed Folder name exist in the Specified folder
        if new_patient_folder_name in os.listdir(SecondLastDir):
            return 1, new_patient_folder_name, Full_Patient_Path_New_folder
        else:
            return 0, new_patient_folder_name, Full_Patient_Path_New_folder




# ##==========================================Anon Function==========================================
def anon_call(path, new_dict_dataset, all_filepaths):
    
    print("\n\n====Anon Called====")
    Dicom_folder_path = path



    # for key in new_dict_dataset:
    #     if key == 0:
    #         print("The values are : ", new_dict_dataset[key])

    # All_dcm = get_All_files(Dicom_folder_path)
    # print("ALL files: in main \n\n")

    # count = 0 
    # for eachFile in All_dcm:
    #     count += 1




    First_Dicom_file = os.path.basename(all_filepaths[0])  

    text = "Hashed"
    Is_hashed, hash_value = check_file_hashed(First_Dicom_file, new_dict_dataset, 0, text)

    if Is_hashed != True:

        print("Is hashed: {} and the hash_value is: {}".format(Is_hashed, hash_value))
        Exist_folder, new_patient_folder_name, Full_Patient_Path_New_folder = check_folder_exist(new_dict_dataset, all_filepaths, Dicom_folder_path, 0)
    
        if Exist_folder == 0 :

            print("Status of folder==========", Exist_folder)
            print("The hashed folder does not exist")
            print("======Creating the new Hashed patient Folder=======")
            Create_New_Folder(new_patient_folder_name, Dicom_folder_path) # calling create_folder function
            # print("Is hashed: {} and the hash_value is: {}".format(Is_hashed, hash_value))


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
                        csv_filename = str("patientHash") + ".csv"
                        # calling create CSV to store the the hashed value
                        create_hash_csv(pname_ID, sha1_pname, csv_filename) 
                        print("Calling WRITE FUNCTION when Csv called")
                        # write_hash_dcm(sha1_pname, Dicom_filename)
                        write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname, new_patient_folder_name)
                    else:
                        print("\n\nFLAG --0000000000000000000000000")
                        print("CSV function not called")
                        print("Calling WRITE FUNCTION when Csv not called")
                        # write_hash_dcm(sha1_pname, Dicom_filename)
                        write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname, new_patient_folder_name)
                else:
                    print("\n\n\n======File {} is a Folder=====".format(Dicom_filename))    #     write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, sha1_pname)
                    print("\n\n\n")
            print("Total files hashed======", count)  
            return Full_Patient_Path_New_folder
        else:
            print("This directory have already been hashed, it is directory ({}). Have overwritten that directory with the new files.".format(new_patient_folder_name))      
            count = 1
            for key in new_dict_dataset:

                Dicom_filename = os.path.basename(all_filepaths[key])
                ds_rtss= LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key)
                pname_ID, sha1_pname, flag = Hash_identifiers(count, ds_rtss)
                write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, hash_value, new_patient_folder_name)
            count = 0
            print("Total files hashed======", count)  
            print("\n\n============Overwrite complete==================")
            return Full_Patient_Path_New_folder
    else:

        print("The files are already Hashed, need to export to the existing New patient folder")

        Exist_folder, new_patient_folder_name, Full_Patient_Path_New_folder = check_folder_exist(new_dict_dataset, all_filepaths, Dicom_folder_path, 1)
        
        for key in new_dict_dataset:

            print("Is hashed: {} and the hash_value is: {}".format(Is_hashed, hash_value))
            print("Patient Identifiers already hashed")
            print("Just overwriting the files without hashing")

            # Exist_folder, new_patient_folder_name = check_folder_exist(new_dict_dataset, all_filepaths, Dicom_folder_path, 1)
            

            if Exist_folder == 0:
                print("Status of folder==========", Exist_folder)
                print("The hashed folder does not exist")
                print("======Creating the new Hashed patient Folder=======")
                Create_New_Folder(new_patient_folder_name, Dicom_folder_path) # calling create_folder function
                Dicom_filename = os.path.basename(all_filepaths[key]) 
                # loading the dicom file content into the dataframe.
                ds_rtss= LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key)
                write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, hash_value, new_patient_folder_name)
                count = 0
                print("Total files hashed======", count)
            else:
                print("Status of folder==========", Exist_folder)
                print("The hashed folder exist")
                Dicom_filename = os.path.basename(all_filepaths[key])
                ds_rtss= LOAD_DCM(Dicom_folder_path,Dicom_filename, new_dict_dataset, key)
                write_hash_dcm(ds_rtss, Dicom_folder_path , Dicom_filename, hash_value, new_patient_folder_name)
                count = 0
                print("Total files hashed======", count)
        return Full_Patient_Path_New_folder

# ===================== Check if the CSV folder exist in hashed patient directory =========== 

def check_CSV_folder_exist(Full_Patient_Path_New_folder):

    if "CSV" in os.listdir(Full_Patient_Path_New_folder):
        return 1
    else:
        return 0


#====================== Initiate the Automation sequence ==========================

def anonymize(path, Datasets, FilePaths,rawdvh):

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


    Full_Patient_Path_New_folder = anon_call(path, new_dict_dataset, all_filepaths)
    print("\n\nThe New patient folder path is : ", Full_Patient_Path_New_folder)

    patient_hash_dvh = os.path.basename(Full_Patient_Path_New_folder)
    print("The HashID for DVh.hash is ::::", patient_hash_dvh)

    Full_Csv_Folder_Path = Full_Patient_Path_New_folder + "/" + "CSV"
    # check if CSV folder exist
    CSV_Folder_exist = check_CSV_folder_exist(Full_Patient_Path_New_folder)
    # if CSV folder does not exist create one
    if CSV_Folder_exist == 0:
        print("The CSV folder path is : ", Full_Csv_Folder_Path)
        os.makedirs(Full_Csv_Folder_Path)
        print("---CSV folder created---")
    else:
        print(":::The CSV folder exist:::")    

    # SecondLastDir = os.path.dirname(path)  # getting path till the second last Folder
    # Full_Patient_Path_New_folder = SecondLastDir + "/" + "64246859-067c-3079-9703-7e71b6869232" + "/" + "CSV" + "/"

    Full_dvhCsv_Folder_Path_ = Full_Patient_Path_New_folder + "/" + "CSV" + "/"
    print("The path for dvh is::::::::::::::::  ",Full_dvhCsv_Folder_Path_)

    Dicom_filename = os.path.basename(all_filepaths[1])
    ds_rtss = LOAD_DCM(path,Dicom_filename, new_dict_dataset, 1)
    # P_ID = ds_rtss.PatientID

    P_HashID = patient_hash_dvh

    print("The patient ID is ::::",P_HashID)
    
    dvh_csv_hash_name = "DVH_" + patient_hash_dvh

    #Calling dvh2csv() function after Anonymization is complete.
    print("CAlling DVH_csv export function")
    dvh2csv(rawdvh, Full_dvhCsv_Folder_Path_, dvh_csv_hash_name, P_HashID)
    print("DVH_csv export function finished")     

    #Calling Pyradiomics after Anonymization is complete.
    print("=====Calling Pyradiomics function====")
    pyradiomics(path, all_filepaths, Full_Patient_Path_New_folder)
    print("Pyradiomics function finished")

    
    



