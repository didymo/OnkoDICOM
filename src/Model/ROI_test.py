import multiprocessing
from src.Model.LoadPatients import *
from src.Model.ROI import *
from src.Model.CalculateDVHs import *
import time
import numpy as np

def list_creator():
    cores = multiprocessing.cpu_count()
    empty_list= []
    for i in range(cores):
        tmp = []
        empty_list.append(tmp)
    return empty_list


def get_shortest(num_list):
    count_list = []
    for i in range(len(num_list)):
        count = sum(num_list[i])
        count_list.append(count)
    shortest_ind = count_list.index(min(count_list))
    return shortest_ind


def task_allocator(dict_NumPoints):
    num_list = list_creator()
    name_list = list_creator()
    for roi in dict_NumPoints:
        curr_points = dict_NumPoints[roi]
        index = get_shortest(num_list)
        num_list[index].append(curr_points)
        name_list[index].append(roi)

    return num_list, name_list





if __name__ == '__main__':
    path = '/home/xudong/Desktop/RawDICOM.India-20191001T080723Z-001/RawDICOM.India'
    dict_ds, dict_path = get_datasets(path)
    rtss = dict_ds['rtss']

    dict_raw_ContourData, dict_NumPoints = get_raw_ContourData(rtss)
    dict_pixluts = get_pixluts(dict_ds)
    roi_info = get_roi_info(rtss)

    roi_selected = []
    for roi in dict_NumPoints:
        print(roi, dict_NumPoints[roi])
        roi_selected.append(roi)

    num_list, name_list = task_allocator(dict_NumPoints)

    print(num_list)
    print(name_list)

    for i in range(len(num_list)):
        print(i, sum(num_list[i]))

    roi_list = roi_selected
    start_time = time.time()
    dict_pixels = get_roi_contour_pixel(dict_raw_ContourData, roi_list, dict_pixluts)
    end_time = time.time()
    print("Time used:", end_time - start_time)


    print("Multiprocessing Start")
    start_time = time.time()

    calc_1 = multiprocessing.Process(name='core_1', target=get_roi_contour_pixel, args=(dict_raw_ContourData, name_list[0], dict_pixluts))
    calc_2 = multiprocessing.Process(name='core_2', target=get_roi_contour_pixel, args=(dict_raw_ContourData, name_list[1], dict_pixluts))
    calc_3 = multiprocessing.Process(name='core_3', target=get_roi_contour_pixel, args=(dict_raw_ContourData, name_list[2], dict_pixluts))
    calc_4 = multiprocessing.Process(name='core_4', target=get_roi_contour_pixel, args=(dict_raw_ContourData, name_list[3], dict_pixluts))

    calc_1.start()
    calc_2.start()
    calc_3.start()
    calc_4.start()

    calc_1.join()
    calc_2.join()
    calc_3.join()
    calc_4.join()


    end_time = time.time()
    print("Multiprocessing End")

    print("Time used:", end_time - start_time)