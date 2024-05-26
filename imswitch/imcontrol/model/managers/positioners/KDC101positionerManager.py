from imswitch.imcommon.model import initLogger
from thorlabs_apt_device.devices.kdc101 import KDC101
from .PositionerManager import PositionerManager
import time

"""
Encoder steps per degree found here:
https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf

Encoder steps per degree for PRMTZ8 is 1919.6418578623391 (rotation stage)
Actuator Z8235B  EncCnt per mm  34554.96  Velocity 772981.3692 (units/s)  Acceleration 263.8443072 (mm/s2)
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
            self.__logger.info(f'Successfully initialized KDC101 (name: {name}) on port {self._port}, waiting 5 seconds')
            time.sleep(5)       # need to wait for the stage to load, otherwise velparams are not available
        except:
            self.__logger.error('Failed to initialize device, check connection and port')

        self._posConvFac = positionerInfo.managerProperties['posConvFac']
        self._velConvFac = positionerInfo.managerProperties['velConvFac']
        self._accConvFac = positionerInfo.managerProperties['accConvFac']
        self.setSpeed(1000, positionerInfo.axes[0])     # setting the default speed to 1000 um/s, hardcoding it for now
        self.setAcceleration(1000, positionerInfo.axes[0])     # setting the default acceleration to 1000 um/s2, hardcoding it for now
        super().__init__(positionerInfo, 
                         name, 
                         initialPosition={axis: self.kdcstage.status['position'] for axis in positionerInfo.axes}#,
                         #initialSpeed={axis: self._unitspers_to_mmpers(self.kdcstage.velparams['max_velocity']) for axis in positionerInfo.axes}
                         )

    def _mm_to_units(self, mm):                 # usually used when stage is controlled from outside
        return int(mm*self._posConvFac)
    
    def _units_to_mm(self, units):              # usually used when status is checked from device
        return units / self._posConvFac
    
    def _mmpers_to_unitspers(self, mmps):       # used when the velocity is set by user, calculating mm/s to units/s
        speed = mmps*(self._velConvFac*0.001)     # 0.001 is to convert um to mm
        print(f'Calculating {mmps} mmps multiplied with {self._velConvFac} to {speed} units/s')
        return mmps*self._velConvFac
    
    def _unitspers_to_mmpers(self, unitspers):       # used when the velocity is status checked, calculating units/s to mm/s
        speed = unitspers/(self._velConvFac*0.001)     # 0.001 is to convert um to mm
        print(f'Calculating {unitspers} units divided by {self._velConvFac} to {speed} um/s')
        return round(speed, 4)
    
    def _mmpers2_to_unitspers2(self, mmps2):       # used when the acceleration is set by user, calculating mm/s2 to units/s2
        acceleration = mmps2*(self._velConvFac*0.001)     # 0.001 is to convert um to mm
        print(f'Calculating {mmps2} mmps multiplied with {self._velConvFac} to {acceleration} units/s2')
        return mmps2*self._velConvFac
    
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
        pos = self._units_to_mm(self.kdcstage.status['position'])
        self.__logger.debug(f'Getting KDC101 position for axis {axis}: {pos} mm')
        return pos

    def finalize(self):
        self.kdcstage.close()
    
    def setSpeed(self, mmps, axis):      # setMove_velocity_in_units
        '''
        Setting the velocity parameters for the stage
        set_velocity_params(acceleration, max_velocity, bay=0, channel=0)
        '''
        self.__logger.debug(f'Changing KDC101 max velocity for axis {axis} to {mmps} ums')
        self.kdcstage.set_velocity_params(self.kdcstage.velparams['acceleration'],
                                          int(self._mmpers_to_unitspers(mmps)))
        
    def setAcceleration(self, mmps2, axis):      # setMove_velocity_in_units
        '''
        Setting the velocity parameters for the stage
        set_velocity_params(acceleration, max_velocity, bay=0, channel=0)
        '''
        self.__logger.debug(f'Changing KDC101 max acceleration for axis {axis} to {mmps2} um/s2')
        self.kdcstage.set_velocity_params(int(self._mmpers2_to_unitspers2(mmps2)),
                                          self.kdcstage.velparams['max_velocity'])
        
    
    #def speed(self, axis):
    #    '''
    #    Get the velocity/speed of the stage
    #    '''
    #    return self._unitspers_to_mmpers(self.kdcstage.velparams['max_velocity'])
    
    #TODO change the acceleration as well


    

'''
"positioners": {
    "sample_stage": {
        "managerName": "KDC101positionerManager",
        "managerProperties": {
            "port": "COM14",
            "units": "mm",
            "posConvFac": 34554.96,
            "velConvFac": 772981.3692,
            "accConvFac": 263.8443072
        },
        "axes": [
          "X"
      ],
      "isPositiveDirection": true,
      "forPositioning": true,
      "forScanning": true
    },
    "camera_stage": {
        "managerName": "KDC101positionerManager",
        "managerProperties": {
            "port": "COM15",
            "units": "mm",
            "posConvFac": 34554.96,
            "velConvFac": 772981.3692,
            "accConvFac": 263.8443072
        },
        "axes": [
          "Y"
      ],
      "isPositiveDirection": true,
      "forPositioning": true,
      "forScanning": true
    }
  },
'''
