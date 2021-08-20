from PySide6 import QtCore, QtGui

import numpy as np
import SimpleITK as sitk

from platipy.dicom.io.crawl import process_dicom_directory
from platipy.imaging.registration.linear import linear_registration
from platipy.imaging.visualisation.utils import (generate_comparison_colormix, return_slice)

def dicom_crawler(filepath, overwrite, output):
    process_dicom_directory(filepath,
                            overwrite_existing_files=overwrite,
                            output_directory = output)


def create_fused_model(old_images, new_image):

    print("fuseTest00")
    
    #fuse images
    fused_image = register_images(old_images, new_image)
    print("fuseTest01")
    
    
    #create colored images
    sp_plane, _, sp_slice = old_images.GetSpacing()
    asp = (1.0*sp_slice)/sp_plane
    
    print("fuseTest1")
    color_axial = get_fused_pixmap(old_images, fused_image, asp, "axial")
    print("fuseTest2")
    color_sagittal = get_fused_pixmap(old_images, fused_image, asp, "sagittal")
    print("fuseTest3")
    color_coronal = get_fused_pixmap(old_images, fused_image, asp, "coronal")
    
    
    return color_axial, color_sagittal, color_coronal




#Can be expanded to peform all of platipy's registrations
def register_images(image_1, image_2):
    img_ct, tfm = linear_registration(
            image_1,
            image_2,
            shrink_factors=[8],
            smooth_sigmas=[10],
            reg_method='rigid',
            verbose = False
        )
    return img_ct






def get_fused_pixmap(orig_image, fused_image, aspect, view):

    # Get a color pixmap.
    # :param sitk image: original 3d image
    # :param sikt image: fused 3d image
    # :param aspect: scaled pixel spacing of first image
    # :return: color pixmap.

    #Get dimension /could also input dimensions as parameters
    image_array = sitk.GetArrayFromImage(orig_image)
    
    axial_width, axial_height = scaled_size(image_array.shape[1]*aspect, image_array.shape[2])
    coronal_width, coronal_height = scaled_size(image_array.shape[1], image_array.shape[0] * aspect)
    sagittal_width, sagittal_height = scaled_size(image_array.shape[2] * aspect, image_array.shape[0])


    slice_axial = int(image_array.shape[0]/2)
    slice_other = int(image_array.shape[1]/2)
    
    #get an array in the form (:, i, :), (i, :, :), (:,:,i)
    if(view == "sagittal"): 
        image_slice = return_slice("x", slice_other)
        
        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice = image_slice))
        
        #pixel_array_color = np.array(np.flip(generate_comparison_colormix([orig_image, fused_image], arr_slice = image_slice)))

        #resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512,345, 3))
    
        #first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color. 
        qimage2 = QtGui.QImage(((255*pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[0],  QtGui.QImage.Format_RGB888)

        #Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)
    
        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    
    ##########################################
    elif(view == "coronal"):
        image_slice = return_slice("y", slice_other)
        
        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice = image_slice))
    
        #resize dimensions to stop image stretch
        pixel_array_color = np.resize(pixel_array_color, (512,345, 3))
        
        
        #first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color. 
        qimage2 = QtGui.QImage(((255*pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[0],  QtGui.QImage.Format_RGB888)

        #Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage2)
    
        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    else: 
        image_slice = return_slice("z", slice_axial)
    
        pixel_array_color = np.array(generate_comparison_colormix([orig_image, fused_image], arr_slice = image_slice))
    
    
        #first adjusts rgb (0,1) scale to greyscale (0,255) then converts type and formats it to color. 
        qimage = QtGui.QImage(((255*pixel_array_color).astype(np.uint8)), image_array.shape[1], image_array.shape[1],  QtGui.QImage.Format_RGB888)
        
        #Then continues to convert to pixmap just like in onko
        pixmap = QtGui.QPixmap(qimage)
    
        pixmap = pixmap.scaled(512, 512, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)

    #Generates an rgb color overlayed image, convert to contiguous array, and also flip the array if it is a coronal (y) or sagittal (x)
    

    return pixmap

def scaled_size(width, height):
    if width > height:
        height = 512/width*height
        width = 512
    else:
        width = 512/height*width
        height = 512
    return width, height
