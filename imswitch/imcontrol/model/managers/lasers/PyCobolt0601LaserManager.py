from imswitch.imcommon.model import initLogger, pythontools
from pycobolt import Cobolt06
from pycobolt import list_lasers
from .LaserManager import LaserManager
import importlib

class PyCobolt0601LaserManager(LaserManager):
    """ LaserManager for Cobolt 06-01 lasers. Uses digital modulation mode when
    scanning. Does currently not support DPL type lasers.

    Manager properties:

    - ``digitalPorts`` -- a string array containing the COM ports to connect
      to, e.g. ``["COM4"]``
    """

    def __init__(self, laserInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        self._port = laserInfo.managerProperties['port']
        self._ttlLine = laserInfo.managerProperties['digitalLine']
        self.__logger.debug(f'Initializing Cobolt0601 laser (name: {name}) on port {self._port}')
        self._is_DPL = False
        if 'DPL' in name:
            self._is_DPL = True
        try:    
            self._laser = Cobolt06(port=self._port)
            self._digitalMod = False

            # start up by turning on modulation power -> laser is off
            self._laser.constant_current(0)
            # check mode of laser
            mode = self._laser.get_mode()

            self.__logger.debug(f'Laser mode is: {mode}, might have to turn the key.')
            super().__init__(laserInfo, name, isBinary=False, valueUnits='mW', valueDecimals=0, isModulated=True)
        
        #TODO mocker does not work
        except Exception as e:
            self.__logger.error(f'Failed to initialize Cobolt0601-DPL laser (name: {name}) on port {self._port}, loading mocker.')
            package = importlib.import_module(
                pythontools.joinModulePath('imswitch.imcontrol.model.lantzdrivers_mock.', 'cobolt0601')
                )
            driver = getattr(package, 'Cobolt0601_f2')
            laser = driver(self._port)
            laser.initialize()

    def setEnabled(self, enabled):      # toggle laser on or off
        if enabled:                             # laser is toggled on 
            self._laser.constant_power()    # set laser to constant power mode
        else:     
            self._laser.constant_current(0)                       # If laser should be disabled, turn off by setting scanmode to active -> modulation mode
            
    def setValue(self, power):
        if self._is_DPL:
            power = int(power)*1000
        else:
            power = int(power)
        self._laser.set_power(power)
        self.__logger.debug(f'Set power to: {power}')

    def setScanModeActive(self, active):            

        if active == False:                      # turn off everything
            self._laser.set_power(0)                # If laser should be disabled, turn off by setting scanmode to active -> modulation mode
        else:
        #TODO
        # this is needed when imswitch is handling the scan
        # for now, arduino is handling the scanning
        # once the camera is not exposing the laser will not be on whilst digital modulation is set
            pass

    def setModulationEnabled(self, enabled):
        if enabled:
            self._laser.power_modulation_mode(digital_enabled=True)
        else:
            self._laser.power_modulation_mode(digital_enabled=False)

    
    def setModulationPower(self, power):
        power = int(power)
        self._laser.set_modulation_power(power)
        self.__logger.debug(f'Set modulation power to: {power}')
    
    def getModulationPower(self):
        return self._laser.get_modulation_power()

    def getAllDeviceNames(self):                    # wonder where thats needed
        self.__logger.debug(f'Available devices: {list_lasers()}')
        return list_lasers()
                            
# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
