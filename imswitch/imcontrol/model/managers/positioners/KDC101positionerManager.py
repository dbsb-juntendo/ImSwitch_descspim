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
In 1 mm there are 34554.96 encoder counts/device units

"""

class KDC101positionerManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):

        self.__logger = initLogger(self)
        self._port = positionerInfo.managerProperties['port']
        try:
            self.__logger.debug(f'Initializing KDC101 (name: {name}) on port {self._port}')
            self.kdcstage = KDC101(serial_port=self._port, home=False)
            self.__logger.info(f'Successfully initialized KDC101 (name: {name}) on port {self._port}, NOT HOMED!')
            time.sleep(1)
            self._posConvFac = positionerInfo.managerProperties['posConvFac']
            self._velConvFac = positionerInfo.managerProperties['velConvFac']
            self._accConvFac = positionerInfo.managerProperties['accConvFac']
            self._initialspeed = positionerInfo.managerProperties.get("initialSpeed")
            self._initialPosition = (self.kdcstage.status['position']/self._posConvFac)*1000   

            #TODO do it properly for the speed etc
            #self.setSpeed(self._initialspeed, positionerInfo.axes[0])     # setting the default speed to 1000 um/s, hardcoding it for now
            #self.setAcceleration(1000, positionerInfo.axes[0])     # setting the default acceleration to 1000 um/s2, hardcoding it for now
            
            self.hard_coded_velparams = {'min_velocity': 0,
                        'max_velocity': 1.5,                 # 1.5 mm/s
                        'acceleration': 2,                   # 2 mm/s2
                        'msg': 'mot_get_velparams',
                        'msgid': 1045,
                        'source': 80,
                        'dest': 1,
                        'chan_ident': 1}
            
            self.hard_coded_jogparams = {'jog_mode': 2,
                        'step_size': 0.05,                      # 50 um or 0.05 mm
                        'min_velocity': 0,
                        'acceleration': 2,                    # 2 um/s2
                        'max_velocity': 1.5,                  # 1.5 um/s
                        'stop_mode': 2,
                        'msg': 'mot_get_jogparams',
                        'msgid': 1048,
                        'source': 80,
                        'dest': 1,
                        'chan_ident': 1}
        
            
            # hard code step size, speed and acceleration
            self.kdcstage.set_velocity_params(self._mmpers2_to_unitspers2(self.hard_coded_velparams['acceleration']), 
                                            self._mmpers_to_unitspers(self.hard_coded_velparams['max_velocity']))
            
            #self.kdcstage.set_jog_params(self._mm_to_units(self.hard_coded_jogparams['step_size']), 
            #                            self._mmpers2_to_unitspers2(self.hard_coded_jogparams['acceleration']), 
            #                            self._mmpers_to_unitspers(self.hard_coded_jogparams['max_velocity']))

            self.__logger.debug(f'Setting KDC101 velocity to {self.hard_coded_velparams["max_velocity"]} um/s and acceleration to {self.hard_coded_velparams["acceleration"]} um/s2')

            super().__init__(positionerInfo, 
                            name, 
                            initialPosition={axis: self.kdcstage.status['position'] for axis in positionerInfo.axes}#,
                            #initialSpeed={axis: self._unitspers_to_mmpers(self.kdcstage.velparams['max_velocity']) for axis in positionerInfo.axes}
                            )

            
        
        except:
            self.__logger.error('Failed to initialize device, check connection and port')


    def _mm_to_units(self, mm):                 # usually used when stage is controlled from outside for moving a distance
        '''
        mm              Distance in mm given by user
        Is translated into device units
        '''
        return int(mm*self._posConvFac)
    
    def _units_to_mm(self, units):              # usually used when status is checked from device for moving a distance
        '''
        units           Distance in device units
        '''
        return units/self._posConvFac        
    
    def _mmpers_to_unitspers(self, mmps):       # used when the velocity is set by user, calculating mm/s to units/s
        speed = int(mmps * self._velConvFac)     
        print(f'Calculating {mmps} mmps multiplied with {self._velConvFac} to {speed} units/s')
        return speed
    
    def _mmpers2_to_unitspers2(self, mmps2):       # used when the acceleration is set by user, calculating mm/s2 to units/s2
        acceleration = int(mmps2*self._accConvFac)  
        print(f'Calculating {mmps2} mmps multiplied with {self._accConvFac} to {acceleration} units/s2')
        return acceleration
    
    def home(self, axis):
        self.__logger.debug(f'Homing KDC101 axis {axis}')
        self.kdcstage.home()
        while self.kdcstage.status['position'] != 0:                     
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: 0')
        self.__logger.debug('KDC101 homing finished')

    # difference between move_jog and move_relative?

    def move(self,axis, dist_um):
        """ Moves the positioner by the specified distance and returns the new
        position. Derived classes will update the position field manually. If
        the positioner controls multiple axes, the axis must be specified.
        In other words: move relative or jogging?
        dist: distance in 
        """
        move_units = self._mm_to_units(dist_um * 0.001)             # converting to mm
        self.__logger.debug(f'Moving KDC101 relative {axis} by {move_units} units or {dist_um} um or {dist_um * 0.001} mm')
        self.kdcstage.move_relative(int(move_units))
        end_position = self.kdcstage.status['position'] + move_units
        while self.kdcstage.status['position'] != end_position:                     
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {end_position}')
        self.__logger.debug(f'KDC101 relative movement finished')

    def setPosition(self, axis, dist_um: float):
        """ Adjusts the positioner to the specified position and returns the
        new position. Derived classes will update the position field manually.
        If the positioner controls multiple axes, the axis must be specified.
        In other words: move absolute to a position in mm
        position: position in mm is converted to um, or moving?
        """
        move_units = self._mm_to_units(dist_um * 0.001)             # converting to mm
        self.__logger.debug(f'Moving KDC101 absolute {axis} by {move_units} units or {dist_um} um or {dist_um * 0.001} mm')
        self.kdcstage.move_absolute(move_units)
        while self.kdcstage.status['position'] != move_units:                     
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {move_units}')
        self.__logger.debug(f'KDC101 absolute movement finished')
    
    def moveAbsolute(self, axis, dist_um):
        move_units = self._mm_to_units(dist_um * 0.001)             # converting to mm
        self.__logger.debug(f'Moving KDC101 absolute {axis} by {move_units} units or {dist_um} um or {dist_um * 0.001} mm')
        self.kdcstage.move_absolute(move_units)
        while self.kdcstage.status['position'] != move_units:                     # doesnt fully work
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {move_units}')
        self.__logger.debug(f'KDC101 absolute movement finished')
    
    def updatePosition(self):
        return self.getPosition()

    def getPosition(self, axis):
        """
        Returns the position of the stage in um
        """
        pos_mm = self._units_to_mm(self.kdcstage.status['position'])    # the stage reads it as units, is then converted to mm and then to um and returned in um
        self.__logger.debug(f'Getting KDC101 position for axis {axis}: {pos_mm} mm or {pos_mm * 1000} um')
        return pos_mm * 1000

    def finalize(self):
        self.kdcstage.close()

    # triggering related functions
    def get_triggerIOconfig(self):
        return self.kdcstage.trigger_params()
    
    def set_triggerIOconfig(self, io_params):
        trig1_mode, trig2_mode = io_params
        self.kdcstage.set_triggerparams(trig1_mode=trig1_mode, 
                                        trig1_polarity=1,
                                        trig2_mode=trig2_mode,
                                        trig2_polarity=1)

    def set_rel_move_params(self, relative_distance):
        '''
        Specify relative move distance of the stage for IO input triggering. See 0x0445 for details.
        relative_distance: distance in um
        '''
        units = int(relative_distance*0.001*self._posConvFac)
        self.__logger.debug(f'relative distance: {units} units corresponding to {(units/self._posConvFac)/0.001} um')
        self.kdcstage.set_moverelparams(relative_distance=units)

        

