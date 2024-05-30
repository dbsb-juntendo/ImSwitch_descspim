# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities. This here is a changed version for Descspim development.

## Installation

Create a conda environment with python=3.10 and install imswitch with ``pip install -e . `` while in the Imswitch_descspim folder. Then, install the requirements with `pip install -r requirements_descspim.txt` and install the thorlabs SDK for the thorlabs scientific camera with ``pip install -e ./thorlabs_tsi_sdk-0.0.8/``. Lastly, clone the repository ``git clone https://gitlab.com/ptapping/thorlabs-apt-device.git`` and install with ``pip install --user ./thorlabs-apt-device`` for the correct KDC101 controller driver (may not be needed). Start imswitch by running ``imswitch`` in said environment and select the configuration file ``descspim.json``.

## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

