import numpy as np
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE, TRIGGER_POLARITY
import tifffile
import os
import time

os.add_dll_directory(os.path.abspath('./imswitch/imcontrol/model/interfaces/thorlabs_tsi_sdk/dll/')) # add the location of the SDK DLLs to the PATH

num_frames = 100
save_path = 'C:/Users/alm/Data/240520/thorlabs_cam_sdk/'
# create folder if it doesn't exist
if not os.path.exists(save_path):
    os.makedirs(save_path)
exposure_time = 10 * 1000 # in miliseconds # convert to microseconds
with TLCameraSDK() as sdk:
    available_cameras = sdk.discover_available_cameras()
    if len(available_cameras) < 1:
        print("no cameras detected")
    
    with sdk.open_camera(available_cameras[0]) as camera:

        camera.exposure_time_us = exposure_time
        camera.operation_mode = 2
        # Acquire an image on the RISING edge of the trigger pulse when trigger polarity is ACTIVE_HIGH
        # Acquire an image on the FALLING edge of the trigger pulse when trigger polarity is ACTIVE_LOW
        camera.trigger_polarity = TRIGGER_POLARITY.ACTIVE_HIGH
        camera.frames_per_trigger_zero_for_unlimited = 0
        camera.image_poll_timeout_ms = 10000
        camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED

        print('exposure time in ms: ',camera.exposure_time_us/1000)
        camera.arm(2)
        
        t0 = time.time()
        camera.issue_software_trigger()
        for i in range(num_frames):
            
            frame = camera.get_pending_frame_or_null()
            
            if frame is not None:
                #print("frame #{} received!, timestamp: {}".format(frame.frame_count, frame.time_stamp_relative_ns_or_null))
                
                image_buffer_copy = np.copy(frame.image_buffer)
                time_after_frame = time.time()
                #print(time_after_frame - t0)
                #print("time taken to get frame in ms: ", (time_after_frame - t0)*1000)
                tifffile.imwrite(save_path + 'frame_' + str(frame.frame_count) + '.tif', image_buffer_copy)
            else:
                print("timeout reached during polling, program exiting...")
                break


