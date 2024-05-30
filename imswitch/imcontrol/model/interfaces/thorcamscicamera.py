from logging import raiseExceptions
import numpy as np
import time
import cv2
import os
import sys
import pathlib
from imswitch.imcommon.model import initLogger
import collections
import threading
# this is called first and then the manager is called

# inspiration  https://github.com/nanophotonics/nplab/blob/master/nplab/instrument/camera/thorlabs/kiralux.py
def configure_path():
    absolute_path_to_dlls = str(pathlib.Path(__file__).resolve().parent)+"\\thorlabs_tsi_sdk\\dll\\"
    os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        # Python 3.8 introduces a new method to specify dll directory
        os.add_dll_directory(absolute_path_to_dlls)
    except AttributeError:
        pass

configure_path()

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE

TAG_BITDEPTH = 32768
TAG_EXPOSURE = 32769


class CameraThorCamSci:
    def __init__(self,cameraNo=None, exposure_time = 10000, gain = 0, frame_rate=-1, blacklevel=100, binning=1, 
                 operation_mode=0, trigger_polarity=0):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        print('interface is called')
        # many to be purged
        self.model = "CameraThorCamSci"
        self.shape = (0, 0)
        
        # set some flags        
        self.is_connected = False
        self.is_streaming = False

        # camera parameters
        self.blacklevel = blacklevel
        self.exposure_time = exposure_time
        self.gain = gain
        self.preview_width = 600
        self.preview_height = 600
        self.frame_rate = frame_rate 
        self.cameraNo = cameraNo

        # for triggering
        self.operation_mode = operation_mode
        self.trigger_polarity = trigger_polarity
        ''' def(arm) 
        Before issuing software or hardware triggers to get images from a camera, prepare it for imaging by calling
        :meth:`arm()<thorlabs_tsi_sdk.tl_camera.TLCamera.arm>`.


        Depending on the :attr:`operation_mode<thorlabs_tsi_sdk.tl_camera.TLCamera.operation_mode>`, either call
        :meth:`issue_software_trigger()<thorlabs_tsi_sdk.tl_camera.TLCamera.issue_software_trigger>` or issue a hardware trigger.

        To start a camera in continuous mode, set the operation_mode to
        SOFTWARE_TRIGGERED, frames_per_trigger_zero_for_unlimited to zero, Arm
        the camera, and then call issue_software_trigger one time. The
        camera will then self-trigger frames until disarm or
        dispose is called.
        
        To start a camera for hardware triggering, set the :attr:`operation_mode<thorlabs_tsi_sdk.tl_camera.TLCamera.operation_mode>` to either
        HARDWARE_TRIGGERED or BULB, :attr:`frames per trigger<thorlabs_tsi_sdk.tl_camera.TLCamera.frames_per_trigger_zero_for_unlimited>` to
        one, :attr:`trigger_polarity`<thorlabs_tsi_sdk.tl_camera.TLCamera.trigger_polarity>` to rising-edge or falling-edge triggered, arm the
        camera, and then issue a triggering signal on the trigger input.
        If any images are still in the queue when calling :meth:`arm()<thorlabs_tsi_sdk.tl_camera.TLCamera.arm>`, they will be considered stale
        and cleared from the queue.
        For more information on the proper procedure for triggering frames and receiving them from the camera, please
        see the Getting Started section.


        GET THE ORDER RIGHT!!!!!

        '''

        #self.trigger_polarity = trigger_polarity

        # reserve some space for the software-based framebuffer
        self.NBuffer = 200
        self.frame_buffer = collections.deque(maxlen=self.NBuffer)
        self.frameid_buffer = collections.deque(maxlen=self.NBuffer)
        self.lastFrameId = -1
        self.lastFrame = None
    
        #%% starting the camera thread
        self.camera = None

        # binning 
        self.binning = binning

        try:
            self._init_cam(cameraNo=self.cameraNo)
        except Exception as e:
            self.__logger.error(e)
            raise Exception("No camera ThorCamSci connected")

    def _init_cam(self, cameraNo=1):
        print('camera is initiated in interfaces')
        # start camera
        self.is_connected = True
        
        # open the first device
        self.sdk = TLCameraSDK()
        cameras = self.sdk.discover_available_cameras()
        self.camera = self.sdk.open_camera(cameras[cameraNo-1])

        self.camera.image_poll_timeout_ms = 2000  # 2 second timeout

        # save these values to place in our custom TIFF tags later
        bit_depth = self.camera.bit_depth
        exposure = self.camera.exposure_time_us

        # initialize a mono to color processor if this is a color self.camera
        is_color_camera = (self.camera.camera_sensor_type == SENSOR_TYPE.BAYER)
        mono_to_color_sdk = None
        mono_to_color_processor = None
        if is_color_camera:
            mono_to_color_sdk = MonoToColorProcessorSDK()
            mono_to_color_processor = mono_to_color_sdk.create_mono_to_color_processor(
                self.camera.self.camera_sensor_type,
                self.camera.color_filter_array_phase,
                self.camera.get_color_correction_matrix(),
                self.camera.get_default_white_balance_matrix(),
                self.camera.bit_depth
            )

        # get framesize 
        self.SensorHeight = self.camera.sensor_height_pixels
        self.SensorWidth = self.camera.sensor_width_pixels

        # set exposure
        self.camera.exposure_time_us=int(self.exposure_time*1000)

        # set gain
        self.camera.gain=int(self.gain)
        
        # set blacklevel
        self.camera.blacklevel=int(self.blacklevel)

        # set triggering parameters
        self.camera.operation_mode = self.operation_mode
        self.camera.trigger_polarity = self.trigger_polarity
        
        # maybe this is not needed here
        if int(self.operation_mode) == 0:            # software triggered
            self.camera.frames_per_trigger_zero_for_unlimited = 0
        elif int(self.operation_mode) == 1:          # hardware triggered
            self.camera.frames_per_trigger_zero_for_unlimited = 1
        elif int(self.operation_mode) == 2:          # bulb
            self.camera.frames_per_trigger_zero_for_unlimited = 1
        #self.camera.arm(2)
        #print('camera is armed')
        # start frame grabber thread
        #self.frameGrabberThread = threading.Thread(target=self.frameGrabber, daemon=True)
        #self.frameGrabberThread.start()
        
    def start_live(self):
        self.__logger.debug("Starting Live Thorcam")  
        if not self.is_streaming:
            self.camera.arm(2)
            print('camera is armed is doing live')
            
            if self.camera.operation_mode == OPERATION_MODE.SOFTWARE_TRIGGERED:
                print('issuing software trigger')
                self.camera.issue_software_trigger()
            # start data acquisition
            self.frameGrabberThread = threading.Thread(target=self.frameGrabber, daemon=True)
            self.frameGrabberThread.start()

    def stop_live(self):
        self.__logger.debug("Stopping Live Thorcam")  
        if self.is_streaming:
            # start data acquisition
            self.is_streaming = False
            self.frameGrabberThread.join()

    def suspend_live(self):
        self.__logger.debug("Suspending Live Thorcam")  
        if self.is_streaming:
            self.is_streaming = False
            self.frameGrabberThread.join()
            self.camera.disarm()
            print('camera is disarmed')


    def prepare_live(self):
        self.__logger.debug("Preparing Live Thorcam")  
        return

    def close(self):
        self.__logger.debug("Closing Thorcam")
        self.camera.dispose()
        
    def set_exposure_time(self,exposure_time):
        self.exposure_time = exposure_time
        self.camera.exposure_time_us=int(exposure_time*1000)
        print('exposure time is set to', exposure_time)

    def set_gain(self,gain):
        self.gain = gain
        self.camera.gain = gain

    def set_frame_rate(self, frame_rate):
        pass
        
    def set_blacklevel(self,blacklevel):
        self.blacklevel = blacklevel
        self.camera.black_level=blacklevel
        
    def set_pixel_format(self,format):
        pass
    
    def setBinning(self, binning=1):
        # Unfortunately this does not work
        # self.camera.BinningHorizontal.set(binning)
        # self.camera.BinningVertical.set(binning)
        self.camera.binx=binning
        self.camera.biny=binning
        self.binning = binning

    def getLast(self, is_resize=True):
        # get frame and save
        return self.lastFrame
        

    def flushBuffer(self):
        self.frameid_buffer.clear()
        self.frame_buffer.clear()
        
    def getLastChunk(self):
        chunk = np.array(self.frame_buffer)
        frameids = np.array(self.frameid_buffer)
        #self.flushBuffer()
        self.__logger.debug("Buffer: "+str(chunk.shape)+" IDs: " + str(frameids))
        return chunk
    
    def setROI(self,hpos=None,vpos=None,hsize=None,vsize=None):
        pass

    def set_operation_mode(self, operation_mode):
        print('disarming camera to change operation mode')
        self.camera.disarm()
        print('setting the operation mode here in thorcamscicamera line 214, also frames_per_trigger', operation_mode)       
        self.camera.operation_mode = int(operation_mode)

        if int(operation_mode) == 0:            # software triggered
            self.camera.frames_per_trigger_zero_for_unlimited = 0
        elif int(operation_mode) == 1:          # hardware triggered
            self.camera.frames_per_trigger_zero_for_unlimited = 1
        elif int(operation_mode) == 2:          # bulb
            self.camera.frames_per_trigger_zero_for_unlimited = 1
        else:
            self.__logger.warning(f'Operation mode {operation_mode} does not exist, must be 0, 1 or 2')
            return False
        
    def set_trigger_polarity(self, trigger_polarity):
        if trigger_polarity not in [0, 1]:
            self.__logger.warning(f'Trigger polarity {trigger_polarity} does not exist, must be 0 or 1')
            return False
        else:
            print('Disarming camera to change Trigger polarity to ', str(int(trigger_polarity)))
            self.camera.disarm()
            self.camera.trigger_polarity = trigger_polarity

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_gain(int(property_value))
        elif property_name == "exposure":
            self.set_exposure_time(int(property_value))
        elif property_name == "blacklevel":
            self.set_blacklevel(int(property_value))
        elif property_name == "roi_size":
            self.roi_size = property_value
        elif property_name == "frame_rate":
            self.set_frame_rate(property_value)
        elif property_name == "image_width":
            property_value = 0        
        elif property_name == "image_height":
            property_value = 0
        elif property_name == "operation_mode":             # new additions
            self.set_operation_mode(int(property_value))
        elif property_name == "trigger_polarity":
            self.set_trigger_polarity(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.camera.Gain.get()
        elif property_name == "exposure":
            property_value = self.camera.ExposureTime.get()
        elif property_name == "blacklevel":
            property_value = self.camera.BlackLevel.get()            
        elif property_name == "image_width":
            property_value = self.camera.Width.get()//self.binning         
        elif property_name == "image_height":
            property_value = self.camera.Height.get()//self.binning
        elif property_name == "roi_size":
            property_value = self.roi_size 
        elif property_name == "frame_Rate":
            property_value = self.frame_rate 
        elif property_name == "operation_mode":
            property_value = self.camera.operation_mode
        elif property_name == "trigger_polarity":
            property_value = self.trigger_polarity
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

            
    def getFrameNumber(self):
        return self.frameNumber 

    def send_trigger(self):
        return

    def openPropertiesGUI(self):
        return
    
    def frameGrabber(self):
        self.is_streaming=True
        while self.is_streaming:
            rawFrameBuffer = self.camera.get_pending_frame_or_null()
            if rawFrameBuffer is not None:
                # store frame
                self.lastFrameId+=1
                self.lastFrame=rawFrameBuffer.image_buffer
                self.frame_buffer.append(self.lastFrame)
                self.frameid_buffer.append(self.lastFrameId)


# Copyright (C) ImSwitch developers 2021
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