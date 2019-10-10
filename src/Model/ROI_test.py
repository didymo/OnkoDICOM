import multiprocessing
from src.Model.LoadPatients import *
from src.Model.ROI import *
from src.Model.CalculateDVHs import *
import time
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

    roi_list = ['rt lung', 'lt lung']
    dict_pixels = get_roi_contour_pixel(dict_raw_ContourData, roi_list, dict_pixluts)

    for i in dict_pixels:
        print(i)
        print(dict_pixels[i])
    # print("Non-multiprocessing Start")
    # start_time = time.time()
    #
    # for curr_slice in dict_pixluts:
    #     dict_rois_contours = get_contour_pixel(dict_raw_ContourData, roi_selected, dict_pixluts, curr_slice)
    #
    # end_time = time.time()
    # print("Non-multiprocessing End")
    #
    # print("Time used:", end_time-start_time)