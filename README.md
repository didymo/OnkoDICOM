# Onko
Onko is an extensible open source radiation therapy research platform based on the DICOM standard. It also functions as a cross-platform DICOM RT viewer.  Onko is written in Python and is built on a number of technologies including: pydicom, Pyqt5, PIL, and matplotlib and runs on Windows, Mac OS X and Linux.  Take a tour of Onko by checking out some screenshots or download your own copy today.

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

`virtualenv --python=python3 envOnkoDICOM`

Activate the virtual environment

`source envOnkoDICOM/bin/activate`

Install the requirements

`pip install -r requirements.txt`

You can execute Onko by running

`python main.py`