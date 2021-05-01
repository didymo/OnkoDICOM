<p align="center"><img src="src/res/images/onkodicom_main_banner.png?raw=true" alt="main-icon-onko-dicom" width="250"></p>

# Onko
OnkoDICOM is am Open Source DICOM-RT viewer with enhanced capabilities that make it useful for research in the field of Radiation Oncology. It was created with Radiation Oncologists to allow Radiation Oncologists to do research on DICOM standard image, but Radiation Therapists and Radiation Physicists will find tools included that are useful when manipulating image sets like DICOM-RT, CT, MRI, and PET.

The enhanced capabilities of OnkoDICOM 
1. pseudo-anonymisation
- at each pseudoanonymisation, the image set is copied to a new directory and the doublet of 'Old_ID':'New_ID' is written into a CSV file that the user can archive securely for future reference if needed.  
3. spreadsheet exports
- DVHs of all ROIs
- PyRadiomics output from all ROIs (currently ~132 features)
- clinical description of the patient's disease which can be updated.
4. ROI manipulation
- rename ROI to Standarised Name (correlated with FMA_ID and customisable)
- delete ROI (for all those 'Rings of Bob' and other ROIs used in plan creation)
- add ROI (at present this requires a RTSTRUCT file be present, uses a pixel value definition and manual cleaning on a single slice)

OnkoDICOM is built on open source technologies, such as pydicom, dicompyler-core, Pyqt5, PIL, and matplotlib. Although built in Python, its forms are cross platform, and  we welcome contributions from the wider community via GitHub https://github.com/didymo/OnkoDICOM.

OnkoDICOM was inspired by the [dicompyler project](https://github.com/bastula/dicompyler).

# Installation
*These instructions are based off this
[comment](https://github.com/didymo/OnkoDICOM/issues/7#issuecomment-552151910)
posted by @sjswerdloff*

Onko can be installed on Ubuntu 18.04, if you do not run Ubuntu you can 
try it on a virtual machine such as [Virtualbox](https://www.virtualbox.org/) 
A premade Ubuntu virtual machine can be downloaded from 
[OSBoxes](https://www.osboxes.org/).

Onko requires virtualenv, python3-dev, gcc and git installed and can be
installed by running this command in the terminal.

`sudo apt install virtualenv git python3-dev gcc`

If you are installing onto Windows, you will need to have installed Visual Studio Build Tools, and a 64-bit version of
Python.

Clone the Onko repository

`git clone https://github.com/didymo/OnkoDICOM.git`

Enter the directory and create a virtual environment with a name of
your choice, in this case it's venv.

`cd OnkoDICOM`

`virtualenv --python=python3 venv`

Note that when cloning into a PyCharm workspace, it is recommended to create a virtual environment from the terminal
_outside_ of PyCharm, as PyCharm's built-in virtual environment creation often leads to issues with the pip version.

Activate the virtual environment

`source venv/bin/activate`

OR for Windows

`venv/Scripts/activate.bat`

Install the requirements

`pip install -r pre-requirements.txt`

`pip install -r requirements.txt`

You can execute Onko by running

`python main.py`


# COMPILATION GUIDE
##### General Steps:
- Ensure you have installed virtualenv with Python 3.7.x
- Create a virtual environment like above and then activate the virtual environment
- Make sure you install pyinstaller
	`pip install pyinstaller`
- Now from here, we will choose the OS and run as follows:

For Windows Users:

`pyinstaller OnkoDICOM-Windows.spec`

For Linux Users:

`pyinstaller OnkoDICOM-Linux.spec`

For Mac Users:

`pyinstaller OnkoDICOM-Darwin.spec`
- Open up the dist folder in the same location as the repository, the distributable application will be in there
###### NOTE
If you are experiencing any issue with opening the application up via the dist folder on Mac,
what you have to do is very simple once we have our bundled App we must enter to its content to the tcl folder.

`cd OnkoDICOM.app/Contents/Resources/tcl`

Open up  `init.tcl`  and find where it says:

`package require -exact Tcl 8.6.8`

We must replace it with:

`package require -exact Tcl 8.5.9`

Once this is done, our application will open normally with a double click.
