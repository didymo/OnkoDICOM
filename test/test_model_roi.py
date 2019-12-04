"""
Created on Thu Dec  5 05:25:04 2019

@author: sjswerdloff
"""

from src.Model.ROI import calculate_matrix
from pydicom import dataset
import numpy as np

def test_calculate_matrix():
    image_ds= dataset.Dataset()
    image_ds.PixelSpacing = [1,1]
    image_ds.ImageOrientationPatient=[1,0,0,0,1,0] 
    image_ds.ImagePositionPatient=[0,0,0]  
    image_ds.Rows=4
    image_ds.Columns=4
    array_x, array_y= calculate_matrix(image_ds)
    assert( np.all(array_x == np.array([0,1,2,3])) )
    assert( np.all(array_y == np.array([0,1,2,3])) )