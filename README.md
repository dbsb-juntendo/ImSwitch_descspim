# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities. This here is a changed version for Descspim development.

## Installation

Create a conda environment with python=3.10 and install imswitch with ``pip install -e . `` while in the Imswitch_descspim folder. Then, install the requirements with `pip install -r requirements.txt` and install the thorlabs SDK for the thorlabs scientific camera with ``pip install -e ./thorlabs_tsi_sdk-0.0.8/``. Lastly, clone the repository ``git clone https://gitlab.com/ptapping/thorlabs-apt-device.git`` and install with ``pip install --user ./thorlabs-apt-device`` for the correct KDC101 controller driver (may not be needed). 

## Prepare configuration file

During the installation, the folder `/Users/Documents/ImSwitchConfig/` in the user's Documents is created, where some pre-made configuration files related to basic imswitch are stored in the subfolder `/imcontrol_setups/`. Copy the configuration files `descspim.json` and `descspim_complete.json` from this repository into the subfolder and, using them, create your own configuration file that matches the laser/camera setup that matches your descspim version. Documentation from the initial imswitch for defining a configuration file can be found [here](https://imswitch.readthedocs.io/en/stable/imcontrol-setups.html). For ImSwitch_descspim, a few device adapters have been added/improved:

- Thorlabs Kiralux scmos camera
- Thorlabs KDC101 stage controller
- Cobolt 06-MLD laser
- Cobolt 06-DPL laser
- AA Opto-electronic AOTF for laser triggering 
- Thorlabs ELL9 filter slider with Arduino triggering

Additionally, widgets have been added:

- ZAlignment widget for calculating relative stage movements of camera and sample stage
- Arduino widget for controlling the ELL9 filter slider and selecting color channels

## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io). This repository is still very much under development!

## Notes

- When using a cobolt DPL laser, the power in mW is converted to mA and sent to the laser, as the set_modulation_power() function is not implemented
- The ttl pins that lead to the lasers should be single digit

## TODO

### important

- switch filter and laser options in widget
- remove operation mode and modulation mode on laser and synchronize this with the record button
- stage movement give a few DU puffer
- display max value while live
- prohibit using the green laser within the first few minutes for warmup (has high power in the beginning  )
- naoari viewer widget to visualize it better with the three colors for example
- make metadata file
- jog mode for the stage, easier to find the sample (two buttons each direction per stage for two different speeds)
- window is frozen while recording, do threading
- add pixel size to recorded data -                 tiff.imwrite(path, image,
                             imagej=True,
                             resolution=(1/0.345, 1/0.345),
                             metadata={'unit':'um', 'axes':'YX'})
- 594 modulation does not work again, there is no power modulation mode from python BUT in the software? email cobolt
- when stopping live mode turn off all lasers (toggle)
- rewrite kdcmanager so that original api file can be used

### less important

- crop
- psf widget
- line widget similar to fiji
- update stages after recording finished
- change window layout for when using a potrait style screen