# Onko
OnkoDICOM was created with Radiation Oncologists to allow Radiation Oncologists to do research on DICOM standard image sets (DICOM-RT, CT, MRI, PET) using open source technologies, such as pydicom, dicompyler-core, Pyqt5, PIL, and matplotlib. OnkoDICOM is cross platform, open source software, and welcomes contributions from the wider community via GitHub https://github.com/didymo/OnkoDICOM.

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

Clone the Onko repository

`git clone https://github.com/didymo/OnkoDICOM.git`

Enter the directory and create a virtual environment with a name of
your choice, in this case it's envOnkoDICOM.

`cd OnkoDICOM`

`virtualenv --python=python3 envOnkoDICOM`

Activate the virtual environment

`source envOnkoDICOM/bin/activate`

Install the requirements

`pip install -r requirements.txt`

You can execute Onko by running

`python main.py`
