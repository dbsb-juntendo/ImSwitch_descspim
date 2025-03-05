# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities. This here is a changed version for Descspim development.

## Installation

- Create conda environment ``conda create -n <name_environment> python=3.10``
- Activate conda environment ``conda activate <name_environment>``
- Situated in a folder where ImSwitch should be installed clone the repository ``git clone https://github.com/dbsb-juntendo/ImSwitch_descspim.git``
- Move into the cloned repository ``cd ./ImSwitch_descspim/``
- Install ImSwitch for descSPIM ``pip install -e .``
- Install all the requirements ``pip install -r requirements.txt``
- Download the thorcam sdk from https://www.thorlabs.us/software_pages/ViewSoftwarePage.cfm?Code=ThorCam
- Unzip thorcam sdk and move into ImSwitch folder (here from downloads folder) ``Expand-Archive -Path C:\Users\alm\Downloads\Scientific_Camera_Interfaces_Windows-2.1.zip .``
- Unzip thorcam python package and move to ImSwitch folder``Expand-Archive -Path '.\Scientific Camera Interfaces\SDK\Python Toolkit\thorlabs_tsi_camera_python_sdk_package.zip' .``
- Move dlls to imswitch/imcontrol/.. (dlls are used by imswitch/imcontrol/model/interfaces/thorcamscicamera.py)``Move-Item -Path '.\Scientific Camera Interfaces\SDK\DotNet Toolkit\dlls\Managed_64_lib\' -Destination .\imswitch\imcontrol\model\interfaces\thorlabs_sdk_dll``
- Install thorcam python package ``pip install -e .\thorlabs_tsi_sdk-0.0.8\ .``

## Prepare configuration file

During the installation, the folder `/Users/Documents/ImSwitchConfig/` in the user's Documents is created, where some pre-made configuration files related to basic imswitch are stored in the subfolder `/imcontrol_setups/`. Copy the configuration file `descspim_complete.json` from this repository into the subfolder and match the COM ports of the hardware devices to the ones in the config file. Documentation from the initial imswitch for defining a configuration file can be found [here](https://imswitch.readthedocs.io/en/stable/imcontrol-setups.html). For ImSwitch_descspim, a few device adapters have been added/improved:

- Thorlabs Kiralux scmos camera
- Thorlabs KDC101 stage controller
- Cobolt 06-MLD laser
- Cobolt 06-DPL laser
- AA Opto-electronic AOTF for laser triggering 
- Thorlabs ELL9 filter slider with Arduino triggering

Additionally, widgets have been added:

- ZAlignment widget for calculating relative stage movements of camera and sample stage
- Arduino widget for controlling the ELL9 filter slider and selecting color channels

## User guide

Start Imswitch from command line while in the <name_environment> with command ``imswitch``. The GUI of ImSwitch can be adapted by the user by dragging the widgets to the desired location. 

### Detector settings

During live mode the operation mode of the detector should be set to 0 (under detector settings). For a recording, set the operation mode to 1.

### Stage settings

For acquiring a 3D-stack, use the Z-Alignment tool widget to set the relative move distances of sample stage and camera stage. First, align the sample at the start position of the stack, fine alignment can be done by moving the camera stage in 5 um steps and save this first position in the Z alignment tool. Then move the sample stage by 500 or 1000 um through the sample (+) and align by using the camera stage. A rough estimate is that per mm traveled by the sample, the camera stage needs to move approximately 300 um. After the camera is aligned, save the second position in the z alignment tool. Select a rough distance (default 1.0 um) and press calculate to find the best fitting relative movements. After that, press Update stages to configure the devices. In the positioner widget, set IO1_mode to ``2 - IN - Relative Move`` for both stages and IO2_mode to ``11 - In Motion`` for the sample stage. 

### Laser settings

For a recording, turn on digital modulation for the laser that is supposed to be used.

## Notes

- When using a cobolt DPL laser, the power in mW is converted to mA and sent to the laser, as the set_modulation_power() function is not implemented
- The ttl pins that lead to the lasers should be single digit

### Changes since last release 18.02.2025

- fixed pixel sizes when opening in fiji
- rewrite kdcmanager so that original api file can be used
- fix error when stage is moving too long, stop the movement
- switch filter and laser options in widget
- threading while "move to pos1" and "move to pos2" in zalignment widget
- when more than 2 channels, interleaved acquisition is not post-processed with tick box in recording widget

## TODO

- rename channel tick box
- dropdown for iomode on 
- dropdown for trigger mode camera

- change position to actual filter in widget
- remove operation mode and modulation mode on laser and synchronize this with the record button
- display max value while live
- prohibit using the green laser within the first few minutes for warmup (has high power in the beginning  )
- napari viewer widget to visualize it better with the three colors for example
- jog mode for the stage, easier to find the sample (two buttons each direction per stage for two different speeds)
- window is frozen while recording, do threading
- in gui scale bar is correct for live imaging but not for snapped images (while they get saved with the right pixel size)
- when stopping live mode turn off all lasers (toggle)
- line widget with plot with psf wwidget
- line widget similar to fiji
- update stages after recording finished


