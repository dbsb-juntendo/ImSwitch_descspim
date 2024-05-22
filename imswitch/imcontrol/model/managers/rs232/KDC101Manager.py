from imswitch.imcommon.model import initLogger
from thorlabs_apt_device.devices.kdc101 import KDC101
"""
Encoder steps per degree found here:
https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf

Encoder steps per degree for PRMTZ8 is 1919.6418578623391 (rotation stage)
Actuator Z8235B  EncCnt per mm  34554.96  Velocity 772981.3692 (mm/s)  Acceleration 263.8443072 (mm/s2)

"""

class tempInfo:
    def __init__(self):
        self.managerProperties = {'port': 'COM15', 'posConvFac': 1919.6418578623391, 'velConvFac': 42941.66, "accConvFac": 14.66}

class KDC101Manager:
    def __init__(self, rs232Info, *args, **kwargs):
        self.__logger = initLogger(self)
        self._port = rs232Info.managerProperties['port']
        try:
            self.__logger.debug(f'Initializing KDC101 on port {self._port}')
            self._device = KDC101(serial_port=self._port)
        except:
            self.__logger.error('Failed to initialize device, check connection and port')
        self.__logger.info(f'Initialized KDC101 on port {self._port}')

        self._posConvFac = rs232Info.managerProperties['posConvFac']
        self._velConvFac = rs232Info.managerProperties['velConvFac']
        self._accConvFac = rs232Info.managerProperties['accConvFac']


    def _toEncPosition(self, units):
        return int(units*self._posConvFac)

    def _toPositionInUnits(self, encPosition):
        return encPosition / self._posConvFac

    def _toEncVelocity(self, unitsPerS):
        return int(unitsPerS*self._velConvFac)

    def _toVelocityInUnits(self, encVelocity):
        return encVelocity / self._velConvFac

    def _toEncAcceleration(self, unitsPerSS):
        return int(unitsPerSS*self._accConvFac)

    def _toAccelerationInUnits(self, encAcceleration):
        return encAcceleration / self._velConvFac

    def home(self):
        self._device.home()

    def moveToInUnits(self, units):
        self._device.move_absolute(self._toEncPosition(units))

    def jog(self, forwardBool=True):
        self._device.move_jog(forwardBool)

    def startRotation(self, forwardBool=True):
        self._device.move_velocity(forwardBool)

    def stopRotation(self):
        self._device.stop()

    def setJogDistanceInUnits(self, distInUnits):
        self._device.set_jog_params(self._toEncPosition(distInUnits),
                                    self._device.jogparams['acceleration'],
                                    self._device.jogparams['max_velocity'])

    def setJogAccelerationInUnits(self, accInUnits):
        self._device.set_jog_params(self._device.jogparams['step_size'],
                                    self._toEncAcceleration(accInUnits),
                                    self._device.jogparams['max_velocity'])

    def setJogVelocityInUnits(self, velInUnits): #Defaults set after original default values
        self._device.set_jog_params(self._device.jogparams['step_size'],
                                    self._device.jogparams['acceleration'],
                                    self._toEncVelocity(velInUnits))

    def setMoveVelocityVelocityInUnits(self, velInUnits):
        self._device.set_velocity_params(self._device.velparams['acceleration'],
                                         self._toEncVelocity(velInUnits))

    def setMoveVelocityAccelerationInUnits(self, accInUnits):
        self._device.set_velocity_params(self._toEncAcceleration(accInUnits),
                                         self._device.velparams['max_velocity'])

    def getPositionInUnits(self):
        return self._toPositionInUnits(self._device.status['position'])


