import multiprocessing
import time
import sys
from src.Model.CalculateDVHs import *
from src.Model.LoadPatients import *

def test_calc_dvhs(rtss, dose, roi, queue, dose_limit=None):
    dvh = {}
    dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)

    print("This is", roi)
    queue.put(dvh)


path = '/home/xudong/Desktop/RawDICOM.India-20191001T080723Z-001/RawDICOM.India'
dict_ds, dict_path = get_datasets(path)
rtss = dict_ds['rtss']
rtdose = dict_ds['rtdose']

roi_info = get_roi_info(rtss)

roi_list = []
for key in roi_info:
    roi_list.append(key)


### Without multiprocessing
start = time.time()
dvhs = calc_dvhs(rtss, rtdose, roi_info)
end = time.time()
print(dvhs)
print("Single Processing: ", end-start)

### Multiprocessing
start = time.time()

dict_dvh = multi_get_dvhs(rtss, rtdose, roi_info)

end = time.time()
print("Multi Processing: ", end-start)
print(dvhs)

