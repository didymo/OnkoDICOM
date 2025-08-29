<p align="center"><img src="res/images/onkodicom_main_banner.png?raw=true" alt="main-icon-onko-dicom" width="250"></p>

# Onko
OnkoDICOM is an Open Source DICOM-RT viewer with enhanced capabilities that make it useful for research in the field of Radiation Oncology. It was created with Radiation Oncologists to allow Radiation Oncologists to do research on DICOM standard image, but Radiation Therapists and Radiation Physicists will find tools included that are useful when manipulating image sets like DICOM-RT, CT, MRI, and PET.

The enhanced capabilities of OnkoDICOM.2020:
1. pseudo-anonymisation
   - at each pseudoanonymisation, the image set is copied to a new directory and the doublet of 'Old_ID':'New_ID' is written into a CSV file that the user can archive securely for future reference if needed.  
2. spreadsheet exports
   - DVHs of all ROIs
   - PyRadiomics output from all ROIs (currently ~132 features)
   - clinical description of the patient's disease which can be updated.
3. ROI manipulation
   - rename ROI to a list of Standardised Names (the provided list is correlated to an FMA_ID and so is customisable to your own usage if needed)
   - delete ROI (for all those 'Rings of Bob' and other ROIs used in plan creation)
   - add ROI (at present this requires a RTSTRUCT file be present, uses a pixel value definition and manual cleaning on a single slice)

OnkoDICOM is built on open source technologies, such as pydicom, dicompyler-core, PySide6, PIL, and matplotlib. Although built in Python, its forms are cross-platform, and we welcome contributions from the wider community via GitHub https://github.com/didymo/OnkoDICOM.

OnkoDICOM was inspired by the [dicompyler project](https://github.com/bastula/dicompyler).

### Installation
Installation instructions for Ubuntu and Windows can be located in [the project's wiki](https://github.com/didymo/OnkoDICOM/wiki/Installation-Instructions).

Note that in order to utilise OnkoDICOM's radiomics toolset, the external program Plastimatch will need to be installed. [Plastimatch installation instructions](https://github.com/didymo/OnkoDICOM/wiki/Installation-Instructions#plastimatch).


### Testing

In the root directory, initiate the virtual environment using:
```
source venv/bin/activate
```

To run the tests run:
```
python -m pytest test/
```

the code coverage reporting is done with
```
pip install pytest-cov
```
found here:
https://pypi.org/project/pytest-cov/

To run the report:
```
python -m pytest --cov=src test/
```

