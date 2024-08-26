import enum
import os
import time
from io import BytesIO
from typing import Dict, Optional, Type, List
import h5py
try:
    import zarr
except:
    pass
import numpy as np
import tifffile as tiff
import cv2

from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.model import initLogger
from ome_zarr.writer import write_multiscales_metadata
from ome_zarr.format import format_from_version
import abc
import logging

from imswitch.imcontrol.model.managers.DetectorsManager import DetectorsManager

logger = logging.getLogger(__name__)


class AsTemporayFile(object):
    """ A temporary file that when exiting the context manager is renamed to its original name. """
    def __init__(self, filepath, tmp_extension='.tmp'):
        if os.path.exists(filepath):
            raise FileExistsError(f'File {filepath} already exists.')
        self.path = filepath
        self.tmp_path = filepath + tmp_extension

    def __enter__(self):
        return self.tmp_path

    def __exit__(self, *args, **kwargs):
        os.rename(self.tmp_path, self.path)


class Storer(abc.ABC):
    """ Base class for storing data"""
    def __init__(self, filepath, detectorManager):
        self.filepath = filepath
        self.detectorManager: DetectorsManager = detectorManager

    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        """ Stores images and attributes according to the spec of the storer """
        raise NotImplementedError

    def stream(self, data = None, **kwargs):
        """ Stores data in a streaming fashion. """
        raise NotImplementedError


class ZarrStorer(Storer):
    """ A storer that stores the images in a zarr file store """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        with AsTemporayFile(f'{self.filepath}.zarr') as path:
            datasets: List[dict] = []
            store = zarr.storage.DirectoryStore(path)
            root = zarr.group(store=store)

            for channel, image in images.items():
                shape = self.detectorManager[channel].shape
                root.create_dataset(channel, data=image, shape=tuple(reversed(shape)),
                                        chunks=(512, 512), dtype='i2') #TODO: why not dynamic chunking?

                datasets.append({"path": channel, "transformation": None})
            write_multiscales_metadata(root, datasets, format_from_version("0.2"), shape, **attrs)
            logger.info(f"Saved image to zarr file {path}")


class HDF5Storer(Storer):
    """ A storer that stores the images in a series of hd5 files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            with AsTemporayFile(f'{self.filepath}_{channel}.h5') as path:
                file = h5py.File(path, 'w')
                shape = self.detectorManager[channel].shape
                dataset = file.create_dataset('data', tuple(reversed(shape)), dtype='i2')
                for key, value in attrs[channel].items():
                    try:
                        dataset.attrs[key] = value
                    except:
                        logger.debug(f'Could not put key:value pair {key}:{value} in hdf5 metadata.')

                dataset.attrs['detector_name'] = channel

                # For ImageJ compatibility
                dataset.attrs['element_size_um'] = \
                    self.detectorManager[channel].pixelSizeUm

                if image.ndim == 3:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2], [2, 1, 0])
                elif image.ndim == 4:
                    dataset[:, ...] = np.moveaxis(image, [0, 1, 2, 3], [3, 2, 1, 0])
                else:
                    dataset[:, ...] = np.moveaxis(image, 0, -1)

                file.close()
                logger.info(f"Saved image to hdf5 file {path}")


class TiffStorer(Storer):
    """ A storer that stores the images in a series of tiff files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            with AsTemporayFile(f'{self.filepath}_{channel}.tiff') as path:

                tiff.imwrite(path, image,
                             imagej=True,
                             resolution=(1/0.345, 1/0.345),
                             metadata={'unit':'um', 'axes':'YX'}
                )
                             
                logger.info(f"Saved image to tiff file {path}")

class PNGStorer(Storer):
    """ A storer that stores the images in a series of png files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            #with AsTemporayFile(f'{self.filepath}_{channel}.png') as path:
            path = f'{self.filepath}_{channel}.png'
            # if image is BW only, we have to convert it to RGB
            if image.dtype == np.float32 or image.dtype == np.float64:
                image = cv2.convertScaleAbs(image)
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            cv2.imwrite(path, image)
            del image
            logger.info(f"Saved image to png file {path}")


class JPGStorer(Storer):
    """ A storer that stores the images in a series of jpg files """
    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        for channel, image in images.items():
            #with AsTemporayFile(f'{self.filepath}_{channel}.jpg') as path:
            path = f'{self.filepath}_{channel}.jpg'
            # if image is BW only, we have to convert it to RGB
            if image.ndim == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            cv2.imwrite(path, image)
            logger.info(f"Saved image to jpg file {path}")
class MP4Storer(Storer):
    """ A storer that writes the frames to an MP4 file """

    def snap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str] = None):
        # not yet implemented
        pass


class SaveMode(enum.Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
    Numpy = 4


class SaveFormat(enum.Enum):
    TIFF = 1
    HDF5 = 2
    ZARR = 3
    MP4 = 4
    PNG = 5
    JPG = 6

class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    UntilStop = 5

DEFAULT_STORER_MAP: Dict[str, Type[Storer]] = {
    SaveFormat.ZARR: ZarrStorer,
    SaveFormat.HDF5: HDF5Storer,
    SaveFormat.TIFF: TiffStorer,
    SaveFormat.MP4: MP4Storer,
    SaveFormat.PNG: PNGStorer,
    SaveFormat.JPG: JPGStorer
}

class RecordingManager(SignalInterface):
    """ RecordingManager handles single frame captures as well as continuous
    recordings of detector data. """
    sigRecordingStarted = Signal()
    sigRecordingEnded = Signal()
    sigRecordingFrameNumUpdated = Signal(int)  # (frameNumber)
    sigRecordingTimeUpdated = Signal(int)  # (recTime)
    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)
    sigMemoryRecordingAvailable = Signal(
        str, object, object, bool
    )  # (name, file, filePath, savedToDisk)

    def __init__(self, detectorsManager, storerMap: Optional[Dict[str, Type[Storer]]] = None):
        super().__init__()
        self.__logger = initLogger(self)
        self.__storerMap = storerMap or DEFAULT_STORER_MAP
        self._memRecordings = {}  # { filePath: bytesIO }
        self.__detectorsManager = detectorsManager
        self.__record = False

    def __del__(self):
        self.endRecording(emitSignal=False, wait=True)
        if hasattr(super(), '__del__'):
            super().__del__()

    @property
    def record(self):
        """ Whether a recording is currently being recorded. """
        return self.__record

    @property
    def detectorsManager(self):
        return self.__detectorsManager

    def getSaveFilePath(self, path, allowOverwriteDisk=False, allowOverwriteMem=False):
        newPath = path
        numExisting = 0

        def existsFunc(pathToCheck):
            if not allowOverwriteDisk and os.path.exists(pathToCheck):
                return True
            if not allowOverwriteMem and pathToCheck in self._memRecordings:
                return True
            return False

        while existsFunc(newPath):
            numExisting += 1
            pathWithoutExt, pathExt = os.path.splitext(path)
            newPath = f'{pathWithoutExt}_{numExisting}{pathExt}'
        return newPath

    def startRecording(self, detectorNames, recMode, savename, 
                       saveMode, attrs, saveFormat=SaveFormat.TIFF, 
                       singleMultiDetectorFile=False, singleLapseFile=False,recFrames=None, recTime=None):
        
        '''
                    self.recordingArgs = {                          # from RecordingController.py 
                'detectorNames': detectorsBeingCaptured,
                'recMode': self.recMode,
                'savename': self.savename,
                'saveMode': SaveMode(self._widget.getRecSaveMode()),
                'saveFormat': SaveFormat(self._widget.getsaveFormat()),
                'attrs': {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                          for detectorName in detectorsBeingCaptured},
                'singleMultiDetectorFile': (len(detectorsBeingCaptured) > 1 and
                                            self._widget.getMultiDetectorSingleFile())
            }
        '''
        self.__logger.info('Starting recording')
        self.__record = True

        self.detectorNames = detectorNames
        self.recMode = recMode
        self.savename = savename
        self.saveMode = saveMode
        self.saveFormat = saveFormat
        self.attrs = attrs
        self.recFrames = recFrames
        self.recTime = recTime
        self.singleMultiDetectorFile = singleMultiDetectorFile
        self.singleLapseFile = singleLapseFile
        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers(),
                                          condition=lambda c: c.forAcquisition)
        
        acqHandle = self.detectorsManager.startAcquisition()    
        try:
            self._record()
        finally:
            self.detectorsManager.stopAcquisition(acqHandle)
            #self.endRecording(emitSignal=True, wait=True)
    @property
    def record(self):
        """ Whether a recording is currently being recorded. """
        return self.__record

    @property
    def detectorsManager(self):
        return self.__detectorsManager
    
    def endRecording(self, emitSignal=True, wait=True):
        self.__detectorsManager.execOnAll(lambda c: c.flushBuffers(),
                                          condition=lambda c: c.forAcquisition)
        #TODO update stages after recording
        #self.__positionersManager.execOnAll(lambda c: c.flushBuffers())
        
        if self.__record:
            self.__logger.info('Stopping recording')
        self.__record = False
        if emitSignal:
            self.sigRecordingEnded.emit()

    def snap(self, detectorNames, savename, saveMode, saveFormat, attrs):
        '''
                self._master.recordingManager.snap(detectorNames,
                                           savename,
                                           SaveMode(self._widget.getSnapSaveMode()),
                                           SaveFormat(self._widget.getsaveFormat()),
                                           attrs)
        '''
        acqHandle = self.__detectorsManager.startAcquisition()
        try:
            self.__logger.info('Snapping')
            images = {}
            for detectorName in detectorNames:
                images[detectorName] = self._getNewFrame(detectorName)
            if saveFormat:
                storer = self.__storerMap[saveFormat]
                if saveMode == SaveMode.Disk or saveMode == SaveMode.DiskAndRAM:
                    # Save images to disk
                    store = storer(savename, self.__detectorsManager)
                    store.snap(images, attrs)
                if saveMode == SaveMode.RAM or saveMode == SaveMode.DiskAndRAM:
                    for channel, image in images.items():
                        name = os.path.basename(f'{savename}_{channel}')
                        self.sigMemorySnapAvailable.emit(name, image, savename, saveMode == SaveMode.DiskAndRAM)
        finally:
            self.__detectorsManager.stopAcquisition(acqHandle)
            if saveMode == SaveMode.Numpy:
                return images            


    def _record(self):
        shapes = {detectorName: self.detectorsManager[detectorName].shape
                  for detectorName in self.detectorNames}
        currentFrame = {}
        datasets = {}
        filenames = {}

        for detectorName in self.detectorNames:
            currentFrame[detectorName] = 0


            # Initial number of frames must not be 0; otherwise, too much disk space may get
            # allocated. We remove this default frame later on if no frames are captured.
            shape = shapes[detectorName]
            if len(shape) > 2:
                shape = shape[-2:]
            
            if self.saveFormat == SaveFormat.TIFF:
                fileExtension = str(self.saveFormat.name).lower()
                filenames[detectorName] = self.getSaveFilePath(
                    f'{self.savename}_{detectorName}.{fileExtension}', False, False)
                
                saving_path_tif = filenames[detectorName][:-5]
                
                # check if path exists and if not create it
                if not os.path.exists(saving_path_tif):
                    self.__logger.info(f'Creating save folder at {saving_path_tif}')
                    os.mkdir(saving_path_tif)
                elif not os.path.exists(saving_path_tif + '_1'):
                    saving_path_tif = saving_path_tif + '_1'
                    self.__logger.info(f'Creating save folder at {saving_path_tif}')
                    os.mkdir(saving_path_tif)
                else:
                    list_ids = [i.split('_')[-1] for i in os.listdir(os.path.dirname(saving_path_tif)) if i.startswith(os.path.basename(saving_path_tif)) and i.split('_')[-1].isdigit()]
                    saving_path_tif = saving_path_tif + '_' + str(int(max(list_ids)) + 1)
                    self.__logger.info(f'Creating save folder at {saving_path_tif}')
                    os.mkdir(saving_path_tif)
            
            elif self.saveFormat == SaveFormat.HDF5:
                self.__logger.error(f'HDF5 format not yet implemented')
            elif self.saveFormat == SaveFormat.ZARR:
                self.__logger.error(f'ZARR format not yet implemented')
            
        self.sigRecordingStarted.emit()
        try:
            if self.recMode == RecMode.SpecFrames:
                if self.recFrames is None:
                    raise ValueError('recFrames must be specified for RecMode.SpecFrames')
                
                # main acquisition loop
                while (self.record and any([currentFrame[detectorName] < self.recFrames for detectorName in self.detectorNames])):
                    for detectorName in self.detectorNames:
                        # get the current image
                        newFrame = self._getNewFrame(detectorName)
                        if newFrame is not None:
                            if self.saveFormat == SaveFormat.TIFF:
                                prefix = f'/image_{currentFrame[detectorName]}.tif'
                                tiff.imwrite(saving_path_tif + prefix, newFrame)
                                currentFrame[detectorName] += 1
                            else:
                                self.__logger.error(f'Other recording formats not yet implemented')
                        else:
                            self.__logger.error(f'Frame None, Timout polling error.')

                            # Things get a bit weird if we have multiple detectors when we report
                            # the current frame number, since the detectors may not be synchronized.
                            # For now, we will report the lowest number.
                            self.sigRecordingFrameNumUpdated.emit(min(list(currentFrame.values())))
                    time.sleep(0.0001)
                self.sigRecordingFrameNumUpdated.emit(0)              
            else:   
                self.__logger.error('Other recording modes not yet implemented')
        finally:
            self.endRecording(emitSignal=True, wait=False)             # self.__recordingManager.endRecording(emitSignal=True, wait=False)

        

    def _getNewFrame(self, detectorName):
        newFrames = self.detectorsManager[detectorName].getLastImage()
        newFrames = np.array(newFrames)
        return newFrames