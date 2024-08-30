from imswitch.imcommon.model import initLogger, pythontools
from pycobolt import Cobolt06DPL
from pycobolt import list_lasers
from .LaserManager import LaserManager
import importlib

class PyCobolt0601DPLLaserManager(LaserManager):
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
        self.__logger.debug(f'Initializing Cobolt0601-DPL laser (name: {name}) on port {self._port}')

        try:    
            self._laser = Cobolt06DPL(self._port)
            self._digitalMod = False

            # start up by turning on modulation power -> laser is off
            self._laser.set_power(5)
            self._laser.modulation_mode()
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
            self._laser.digital_modulation(0)   # turn off dig. modulation
            self._laser.constant_power()    # set laser to constant power mode
        else:                                   # If laser should be disabled, turn off by setting scanmode to active -> modulation mode
            self._laser.modulation_mode()   # switch to modulation mode
            self._laser.digital_modulation(0)   # but make sure to have digital modulation off
            
    def setValue(self, power):
        power = int(power)*1000
        self._laser.set_power(power)
        self.__logger.debug(f'Set power to: {power}')

    def setScanModeActive(self, active):            

        if active == False:                      # turn off everything
            self._laser.digital_modulation(0)    # turn off dig. modulation
            self._laser.modulation_mode(0)
        else:
        #TODO
        # this is needed when imswitch is handling the scan
        # for now, arduino is handling the scanning
        # once the camera is not exposing the laser will not be on whilst digital modulation is set
            pass

    def setModulationEnabled(self, enabled):
        if enabled:
            self._laser.modulation_mode()
            self._laser.digital_modulation(1)
        else:
            self._laser.digital_modulation(0)

    
    def setModulationPower(self, power):
        #TODO contact cobolt, as set_modulation_power() function is not implemented for DPL lasers
        # need to use set_modulation_current_high() and set_modulation_current_low() functions
        # y = 9.3916x + 1219.3
        mA = (9.3916*power) + 1219.3
        self._laser.set_modulation_current_high(mA+(mA*0.05)) # 5% higher than the desired value
        self._laser.set_modulation_current_low(0)
        self.__logger.debug(f'Desired power: {power}, set modulation current to: {mA} +/- 5%')

    def getModulationPower(self):
        #TODO contact cobolt, as set_modulation_power() function is not implemented for DPL lasers
        # need to use set_modulation_current_high() and set_modulation_current_low() functions
        # y = 9.3916x + 1219.3
        high, low = self._laser.get_modulation_current()
        power = ((high - 1219.3) / 9.3916)
        return power

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
