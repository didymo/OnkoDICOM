def dvh2pandas(dict_dvh, patient_id):
    """
    Convert dvh data to pandas Dataframe.
    :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
    :param patient_id: Patient Identifier
    :return: pddf, dvh data converted to pandas Dataframe
    """
    csv_header = []
    csv_header.append('Patient ID')
    csv_header.append('ROI')
    csv_header.append('Volume (mL)')

    #max_roi_dose = 0

    dvh_csv_list = []

    # for i in dict_dvh:
    #     dvh_roi_list = []
    #     dvh = dict_dvh[i]
    #     name = dvh.name
    #     volume = dvh.volume
    #     dvh_roi_list.append(patient_id)
    #     dvh_roi_list.append(name)
    #     dvh_roi_list.append(volume)
    #     dose = dvh.relative_volume.counts

    #     for i in range(0, len(dose), 10):
    #         dvh_roi_list.append(dose[i])
    #         # Update the maximum dose value, if current dose
    #         # exceeds the current maximum dose
    #         if i > max_roi_dose:
    #             max_roi_dose = i

    #     dvh_csv_list.append(dvh_roi_list)

    #for i in range(0, max_roi_dose + 1, 10):
    #    csv_header.append(str(i) + 'cGy')

    #CHANGE DVH.CSV EXPORT
    
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

        current_cGy_list = []
        current_percentage_range = 100
        for i in range(0, len(dose), 10):
            if (current_percentage_range < 0)
                break
            if (dose[i] >= current_percentage_range)
                cGy = str(i) + 'cGy: ' + str(dose[0])
                current_cGy_list.append(cGy)
            else
                dvh_roi_list.append(current_cGy_list)
                current_percentage_range = current_percentage_range - 0.5                

        dvh_csv_list.append(dvh_roi_list)
    
    #Column in percentage %
    for i in np.arange(100, 0 - 0.5, -0.5):
        csv_header.append(str(i) + '%')
    
    #CHANGE DVH.CSV EXPORT

    # Convert the list into pandas dataframe, with 2 digit rounding.
    pddf = pd.DataFrame(dvh_csv_list, columns=csv_header).round(2)
    # Fill empty blocks with 0.0
    pddf.fillna(0.0, inplace=True)
    pddf.set_index('Patient ID', inplace=True)

    # Return pandas dataframe
    return pddf
