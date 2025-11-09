# **💤 Sleep Enforcer**

A simple Python desktop application to enforce healthier sleep habits by  
prompting for a reason to stay up and hibernating the computer if no  
valid reason is given.

## **Features**

* Gives a 5-minute warning before shutdown time.  
* Prompts for a valid reason to stay awake.  
* Grants a 30-minute extension for valid reasons.  
* Shows a 60-second final countdown before hibernating.  
* Cross-platform (built with Tkinter).

## **How to Run from Source**

This project requires [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

1. Clone the repository:  
   git clone \[https://github.com/Overwatch886/sleep-enforcer.git\] (https://github.com/Overwatch886/sleep-enforcer.git)  
   cd sleep-enforcer

2. Create and activate the Conda environment:  
   \# This reads the environment.yml file, creates the 'sleep\_enforcer\_env',  
   \# and installs all dependencies (Python, Pillow) in one step.  
   conda env create \-f environment.yml

   \# Activate the new environment  
   conda activate sleep\_enforcer\_env

3. Run the application:  
   \# Make sure your (sleep\_enforcer\_env) is active  
   python sleep\_enforcer\_refactored.py

## **How to Build**

This project can be built into a standalone executable using PyInstaller.

1. Activate your environment:  
   conda activate sleep\_enforcer\_env

2. Install PyInstaller in your environment:  
   \# PyInstaller is best installed with pip, even in a conda env  
   pip install pyinstaller

3. Run the build command:  
   \# Make sure your icon is in an 'icons' folder  
   pyinstaller \--onefile \--windowed \--add-data "icons;icons" sleep\_enforcer\_refactored.py

