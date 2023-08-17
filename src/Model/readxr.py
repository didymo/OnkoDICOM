import matplotlib.pyplot as plt
import pydicom
from pydicom import dcmread

fname = "IM00001"
file = dcmread(fname)
plt.imshow(file.pixel_array, cmap=plt.cm.bone)
plt.show()