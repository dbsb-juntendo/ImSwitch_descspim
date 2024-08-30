from imswitch.imcommon.model import initLogger, pythontools
from aaopto_aotf.aotf import MPDS
from aaopto_aotf.device_codes import BlankingMode, VoltageRange, InputMode
from .LaserManager import LaserManager
import importlib

class PyAAOPTOLaserManager(LaserManager):
    """ LaserManager for channel of AAoptoelectronics AOTF. Uses digital modulation mode when
    scanning. 

    Manager properties:

    
    - ``digitalPorts`` -- a string array containing the COM ports to connect
      to, e.g. ``["COM4"]``
    """

    def __init__(self, laserInfo, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)

        #TODO for now only one channel can be implemented
        #TODO implement multiple channels while using the same port for all of them
        self._port = laserInfo.managerProperties['port']
        self._ttlLine = laserInfo.managerProperties['digitalLine']
        self._channel = laserInfo.managerProperties['channel']
        self._frequency = laserInfo.managerProperties['frequency']
        self._valueUnits='dBm'
        self.__logger.debug(f'Initializing AOTF channel (name: {name}) on port {self._port}')

        try:    
            self._aotf = MPDS(self._port)
            self._digitalMod = False

            # start up by turning on modulation power -> laser is off
            self._aotf.set_blanking_mode(BlankingMode.INTERNAL)
            self._aotf.set_external_input_voltage_range(VoltageRange.ZERO_TO_FIVE_VOLTS)
            self._aotf.set_channel_input_mode(self._channel, InputMode.INTERNAL)
            self._aotf.set_frequency(self._channel, self._frequency)

            super().__init__(laserInfo, name, isBinary=False, valueUnits='dBm', valueDecimals=0, isModulated=True)
        
        #TODO mocker does not work
        except Exception as e:
            self.__logger.error(f'Failed to initialize Cobolt0601-DPL laser (name: {name}) on port {self._port},.')

    def setEnabled(self, enabled):      # toggle laser on or off
        if enabled:                             # laser is toggled on 
            self._aotf.set_channel_input_mode(self._channel, InputMode.INTERNAL) 
            self._aotf.enable_channel(self._channel)   # turn off dig. modulation
        else:                                   # If laser should be disabled, turn off by setting scanmode to active -> modulation mode
            self._aotf.disable_channel(self._channel)
            
    def setValue(self, power):      # power in dBm
        self._aotf.set_power_dbm(self._channel, power)
        self.__logger.debug(f'Set power to: {power} dBm')

    def setScanModeActive(self, active):            
        if active == False:                      # turn off everything
            self._aotf.set_channel_input_mode(self._channel, InputMode.INTERNAL)
            self._aotf.disable_channel(self._channel)    # turn off dig. modulation
        else:
        #TODO
        # this is needed when imswitch is handling the scan
        # for now, arduino is handling the scanning
        # once the camera is not exposing the laser will not be on whilst digital modulation is set
            pass

    def setModulationEnabled(self, enabled):
        if enabled:
            self._aotf.disable_channel(self._channel)
            self._aotf.set_channel_input_mode(self._channel, InputMode.EXTERNAL)
        else:
            self._aotf.disable_channel(self._channel)
            self._aotf.set_channel_input_mode(self._channel, InputMode.INTERNAL)
    
    def setModulationPower(self, power):
        self.__logger.debug(f'Set modulation power to: {power} dBm')
        self.setValue(power)

    def getModulationPower(self):
        return self._aotf.get_power_dbm(self._channel)
                            
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
