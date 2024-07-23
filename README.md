# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities. This here is a changed version for Descspim development.

## Installation

Create a conda environment with python=3.10 and install imswitch with ``pip install -e . `` while in the Imswitch_descspim folder. Then, install the requirements with `pip install -r requirements_descspim.txt` and install the thorlabs SDK for the thorlabs scientific camera with ``pip install -e ./thorlabs_tsi_sdk-0.0.8/``. Lastly, clone the repository ``git clone https://gitlab.com/ptapping/thorlabs-apt-device.git`` and install with ``pip install --user ./thorlabs-apt-device`` for the correct KDC101 controller driver (may not be needed). Start imswitch by running ``imswitch`` in said environment and select the configuration file ``descspim.json``.

## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io). This repository is still very much under development!

## Notes

- When using a cobolt DPL laser, the power in mW is converted to mA and sent to the laser, as the set_modulation_power() function is not implemented
- The ttl pins that lead to the lasers should be single digit

## TODO

### important

- jog mode for the stage, easier to find the sample (two buttons each direction per stage for two different speeds)
- window is frozen while recording, do threading

### less important

- 2024-07-23 12:22:32 WARNING [ThorCamSciManager -> thorlabscam] Property gain does not exist, 2024-07-23 12:22:32 WARNING [ThorCamSciManager -> thorlabscam] Property blacklevel does not exist, remove blacklevel and gain from camera features
- psf widget
- line widget similar to fiji
- update stages after recording finished
- change window layout for when using a potrait style screen