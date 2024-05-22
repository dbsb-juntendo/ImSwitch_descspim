from imswitch.imcommon.model import initLogger
from thorlabs_apt_device.devices.kdc101 import KDC101
from .PositionerManager import PositionerManager

"""
Encoder steps per degree found here:
https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf

Encoder steps per degree for PRMTZ8 is 1919.6418578623391 (rotation stage)
Actuator Z8235B  EncCnt per mm  34554.96  Velocity 772981.3692 (mm/s)  Acceleration 263.8443072 (mm/s2)
EncCnt Encoder count -> 1 unit is 1 mm /34554.96 = 28.93940552 nm

"""

#class tempInfo:
#    def __init__(self):
#        self.managerProperties = {'port': 'COM15', 'posConvFac': 1919.6418578623391, 'velConvFac': 42941.66, "accConvFac": 14.66}

class KDC101positionerManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):

        self.__logger = initLogger(self)
        self._port = positionerInfo.managerProperties['port']
        try:
            self.__logger.debug(f'Initializing KDC101 (name: {name}) on port {self._port}')
            self.kdcstage = KDC101(serial_port=self._port)
        except:
            self.__logger.error('Failed to initialize device, check connection and port')
        self.__logger.info(f'Initialized KDC101 (name: {name}) on port {self._port}')

        self._posConvFac = positionerInfo.managerProperties['posConvFac']
        self._velConvFac = positionerInfo.managerProperties['velConvFac']
        self._accConvFac = positionerInfo.managerProperties['accConvFac']

        super().__init__(positionerInfo, name, initialPosition={axis: self.kdcstage.status['position'] for axis in positionerInfo.axes})

    def _mm_to_units(self, mm):                 # usually used when stage is controlled from outside
        return int(mm*self._posConvFac)
    
    def _units_to_mm(self, units):              # usually used when status is checked from device
        return units / self._posConvFac
    
    def _mmpers_to_unitspers(self, mmps):       # used when the velocity is set by user, calculating mm/s to units/s
        return int(mmps*self._velConvFac)
    
    def _unitspers_to_mmpers(self, unitspers):       # used when the velocity is status checked, calculating units/s to mm/s
        return int(unitspers/self._velConvFac)
    
    def home(self):
        self.kdcstage.home()

    # difference between move_jog and move_relative?

    def move(self, dist, axis):
        """ Moves the positioner by the specified distance and returns the new
        position. Derived classes will update the position field manually. If
        the positioner controls multiple axes, the axis must be specified.
        In other words: move relative or jogging?
        dist: distance in mm, is converted to um
        """
        um = dist/1000
        self.__logger.debug(f'Moving KDC101 {axis} by {um} mm')
        self.kdcstage.move_relative(self._mm_to_units(um))

    def setPosition(self, position: float, axis: str):
        """ Adjusts the positioner to the specified position and returns the
        new position. Derived classes will update the position field manually.
        If the positioner controls multiple axes, the axis must be specified.
        In other words: move absolute to a position in mm
        position: position in mm is converted to um, or moving?
        """
        um = position/1000
        self.kdcstage.move_absolute(self._mm_to_units(um))
    
    def updatePosition(self):
        return self.getPosition()

    def getPosition(self, axis):
        self.__logger.debug(f'Getting KDC101 position for axis {axis}')
        return self._units_to_mm(self.kdcstage.status['position'])

    def finalize(self):
        self.kdcstage.close()
    
    def setSpeed(self, axis, mmps):      # setMove_velocity_in_units
        '''
        Setting the velocity parameters for the stage
        set_velocity_params(acceleration, max_velocity, bay=0, channel=0)
        '''
        self.__logger.debug(f'Changing KDC101 max velocity for axis {axis} to {mmps} mm/s')
        self.kdcstage.set_velocity_params(self.kdcstage.velparams['acceleration'],
                                          self._mmpers_to_unitspers(mmps))
        
    
    def speed(self, axis):
        '''
        Get the velocity/speed of the stage
        '''
        return self._unitspers_to_mmpers(self.kdcstage.velparams['max_velocity'])
    
    #TODO change the acceleration as well


    


