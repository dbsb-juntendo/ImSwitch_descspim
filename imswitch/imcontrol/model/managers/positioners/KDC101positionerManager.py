from imswitch.imcommon.model import initLogger
from thorlabs_apt_device.devices.kdc101 import KDC101
from thorlabs_apt_device import protocol as apt
from thorlabs_apt_device.enums import EndPoint
from .PositionerManager import PositionerManager
import time
"""
Encoder steps per degree found here:
https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf

Encoder steps per degree for PRMTZ8 is 1919.6418578623391 (rotation stage)
Actuator Z8235B  EncCnt per mm  34554.96  Velocity 772981.3692 (units/s)  Acceleration 263.8443072 (mm/s2)
EncCnt Encoder count -> 1 unit is 1 mm /34554.96 = 28.93940552 nm
In 1 mm there are 34554.96 encoder counts/device units

This manager has been written based on the thorlabs_apt_device library (https://thorlabs-apt-device.readthedocs.io/en/latest/index.html)
"""
class KDC101_triggered(KDC101):
    """
    An adapted KDC101 class to include trigger parameters such as 
    - relative distance covered by the stage when IO triggered
    - trigger parameters such as mode and polarity for IO1 and IO2
    - processing of message of both parameters
    """
    def __init__(self, serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number="27",
                 location=None, home=True, invert_direction_logic=True, swap_limit_switches=True):
                 
        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product,
                         serial_number=serial_number, location=location, home=home,
                         invert_direction_logic=invert_direction_logic, swap_limit_switches=swap_limit_switches)
                         
        # own parameters
        self.moverelparams_ = [[{                # 0x0445
            "relative_distance" : 0,
            "msg" : "",
            "msgid" : 0,
            "dest" : 0,
            "source" : 0,
            "chan_ident" : 0,
            } for _ in self.channels] for _ in self.bays]
        
        # Request mot_req_moverelparams
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_moverelparams(source=EndPoint.HOST, dest=bay, chan_ident=channel))


        self.trigger_params_ = [[{              # 0x0524
            # Actual integer code returned by device
            # Unpacked meaning of mode bits
            "trig1_mode" : "",
            "trig1_polarity" : "",
            "trig2_mode" : "",
            "trig2_polarity" : "",
            # Update message fields
            "msg" : "",
            "msgid" : 0,
            "source" : 0,      
            "dest" : 0,        
            "chan_ident" : 0,
        } for _ in self.channels] for _ in self.bays]

        # Request current trigger modes
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.mot_req_kcubetrigconfig(source=EndPoint.HOST, dest=bay, chan_ident=channel))

    def _process_message(self, m):
        super()._process_message(m)
        if m.msg in ("mot_get_kcubetrigconfig","mot_get_moverelparams"):
            # Check if source matches one of our bays
            try:
                bay_i = self.bays.index(m.source)
            except ValueError:
                # Ignore message from unknown bay id
                self._log.warn(f"Message {m.msg} has unrecognised source={m.source}.")
                bay_i = 0
            # Check if channel matches one of our channels
            try:
                channel_i = self.channels.index(m.chan_ident)
            except ValueError:
                # Ignore message from unknown channel id
                self._log.warn(f"Message {m.msg} has unrecognised channel={m.chan_ident}.")
                channel_i = 0

        if m.msg == "mot_get_moverelparams":
            self.moverelparams_[bay_i][channel_i].update(m._asdict())
        elif m.msg == "mot_get_kcubetrigconfig":
            self.trigger_params_[bay_i][channel_i].update(m._asdict())
        else:
            pass

    def set_moverelparams(self, relative_distance=0, bay=0, channel=0):
        """
        Used to set the relative move parameters for the specified motor
        channel. The only significant parameter currently is the relative
        move distance itself. This gets stored by the controller and is used
        the next time a relative move is initiated. See 0x0445

        :param relative_distance:    The distance to move. 
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Setting relative move parameters to relative_distance: {relative_distance} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_moverelparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], relative_distance=relative_distance))
        # Update status with new parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_moverelparams(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

    def set_triggerparams(self, trig1_mode=0, trig1_polarity=0, trig2_mode=0, trig2_polarity=1, bay=0, channel=0):
        """
        The K-Cube motor controllers have two bidirectional trigger ports
        (TRIG1 and TRIG2) that can be used to read an external logic signal
        or output a logic level to control external equipment. Either of them
        can be independently configured as an input or an output and the
        active logic state can be selected High or Low to suit the
        requirements of the application. Electrically the ports output 5 Volt
        logic signals and are designed to be driven from a 5 Volt logic.
        When the port is used in the input mode, the logic levels are TTL
        compatible, i.e. a voltage level less than 0.8 Volt will be recognised
        as a logic LOW and a level greater than 2.4 Volt as a logic HIGH. The
        input contains a weak pull-up, so the state of the input with nothing
        connected will default to a logic HIGH. The weak pull-up feature
        allows a passive device, such as a mechanical switch to be
        connected directly to the input.
        When the port is used as an output it provides a push-pull drive of 5
        Volts, with the maximum current limited to approximately 8 mA.
        The current limit prevents damage when the output is accidentally
        shorted to ground or driven to the opposite logic state by external
        circuity. See 0x0523

        #TODO add more explanation
        :param trig1_mode:          The mode of the trigger 1 port.             Mode IN relative move = 2, Mode OUT - In Motion = 11
        :param trig1_polarity:      The polarity of the trigger 1 port.         Polarity HIGH = 1, Polarity LOW = 2
        :param trig2_mode:          The mode of the trigger 2 port.
        :param trig2_polarity:      The polarity of the trigger 2 port.
        :param bay:                 Index (0-based) of controller bay to send the command.
        :param channel:             Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Setting trigIO parameters: trig1_mode={trig1_mode}, trig1_polarity={trig1_polarity}, trig2_mode={trig2_mode}, trig2_polarity={trig2_polarity} [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mot_set_kcubetrigioconfig(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], trig1_mode=trig1_mode, trig1_polarity=trig1_polarity, trig2_mode=trig2_mode, trig2_polarity=trig2_polarity))
        # Update status with new parameters
        self._loop.call_soon_threadsafe(self._write, apt.mot_req_kcubetrigconfig(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

    


class KDC101positionerManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):

        self.__logger = initLogger(self)
        self._port = positionerInfo.managerProperties['port']
        try:
            self.__logger.debug(f'Initializing KDC101 (name: {name}) on port {self._port}')
            self.kdcstage = KDC101_triggered(serial_port=self._port, home=False)
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
            
            self.timeout = 30   # 30 seconds timeout for moving
            
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
        start_time = time.time()
        while self.kdcstage.status['position'] != end_position:
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {end_position}')
            if time.time() - start_time > self.timeout:
                self.__logger.warning(f'Movement timeout after {self.timeout} seconds. Target position not reached.')
                return
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
        start_time = time.time()
        while self.kdcstage.status['position'] != move_units:                     
        #while self.kdcstage.status['position'] < move_units - 2 or self.kdcstage.status['position'] > move_units + 2 or self.kdcstage.status['position'] != 0:
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {move_units}')
            if time.time() - start_time > self.timeout:
                self.__logger.warning(f'Movement timeout after {self.timeout} seconds. Target position not reached.')
                return
        self.__logger.debug(f'KDC101 absolute movement finished')
    
    def moveAbsolute(self, axis, dist_um):
        move_units = self._mm_to_units(dist_um * 0.001)             # converting to mm
        self.__logger.debug(f'Moving KDC101 absolute {axis} by {move_units} units or {dist_um} um or {dist_um * 0.001} mm')
        self.kdcstage.move_absolute(move_units)
        start_time = time.time()
        while self.kdcstage.status['position'] != move_units:                     # doesnt fully work
        #while self.kdcstage.status['position'] < move_units - 2 or self.kdcstage.status['position'] > move_units + 2 or self.kdcstage.status['position'] != 0:       
            time.sleep(0.5)
            self.__logger.debug(f'Current position: {self.kdcstage.status["position"]}, end position: {move_units}')
            if time.time() - start_time > self.timeout:
                self.__logger.warning(f'Movement timeout after {self.timeout} seconds. Target position not reached.')
                return
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
        return self.kdcstage.trigger_params_
        

    def get_rel_move_params(self):
        rel_distance = self.kdcstage.moverelparams_[0][0]['relative_distance']
        return self._units_to_mm(rel_distance)*1000
    
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

        

