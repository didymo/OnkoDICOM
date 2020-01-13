# Onko
OnkoDICOM was created for Radiation Oncologists to do research using the DICOM standard. OnkoDICOM uses many technologies, including: pydicom, dicompyler-core, Pyqt5, PIL, and matplotlib. OnkoDICOM is cross platform, open source and welcomes contributions from the wider community. OnkoDICOM was inspired by dicompyler.

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
