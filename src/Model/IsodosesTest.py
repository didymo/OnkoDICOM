from src.Model.CalculateImages import convert_raw_data
from src.Model.LoadPatients import get_datasets
import numpy as np
import matplotlib.pyplot as plt

def main():
    path = '/home/xudong/Desktop/RawDICOM.India-20191001T080723Z-001/RawDICOM.India'
    dict_ds, dict_path = get_datasets(path)
    np_pixels = convert_raw_data(dict_ds)
    max = np.amax(np_pixels)
    min = np.amin(np_pixels)
    temp = np_pixels[0]
    print(temp)
    print(type(temp))
    print('max = ', max)
    print('min = ', min)

    print(np.where(np_pixels[0] > 700))
    points = np.where(np_pixels[0].transpose() > 1100)
    print(temp[511][511])
    plt.scatter(points[0], 511 - points[1])
    plt.show()

if __name__ == '__main__':
    main()