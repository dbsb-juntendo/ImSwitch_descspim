from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtCore import pyqtSlot


class Worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, positionerManager, operation, axis, dist=None):
        super().__init__()
        self.positionerManager = positionerManager
        self.operation = operation
        self.axis = axis
        self.dist = dist

    def run(self):
        try:
            if self.operation == 'move':
                self.positionerManager.move(self.axis, self.dist)
            elif self.operation == 'home':
                self.positionerManager.home(self.axis)
            elif self.operation == 'moveAbsolute':
                self.positionerManager.moveAbsolute(self.axis, self.dist)
            elif self.operation == 'setPosition':
                self.positionerManager.setPosition(self.axis, self.dist)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    '''
    # trigger stuff
    def set_IO_params(self, positionerName, axis):
        io_params = self._widget.getIOparams(positionerName, axis)
        self.__logger.debug(f"Setting IO params for {positionerName}, axis {axis}, trig1_mode {io_params[0]}, trig2_mode {io_params[1]}, hardcoding polarity HIGH.")
        self._master.positionersManager[positionerName].set_triggerIOconfig(io_params)
    '''

class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False
        self.thread = None
        self.worker = None
        self.thread_running = False
        self.trigger_options = self._widget.trigger_options

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            speed = hasattr(pManager, 'speed')
            self._widget.addPositioner(pName, pManager.axes, speed)
            axis = pManager.axes[0]                                                     # on this KDC101 stage is only one axis
            self.setSharedAttr(pName, axis, _positionAttr, pManager.position[axis])
            # set IO params
            self._widget.setIOparams1(pName, axis, int(self.trigger_options[0][0]))
            self._widget.setIOparams2(pName, axis, int(self.trigger_options[0][0]))
            if speed:
                self.setSharedAttr(pName, axis, _positionAttr, pManager.speed)



        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigSetSpeed.connect(lambda speed: self.setSpeedGUI(speed, axis))
        self._commChannel.sigUpdateStagePosition.connect(self.updatePosition)               # for the zalignment widget
        self._commChannel.sigUpdateRelDistance.connect(self.updateRelDistance)

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        #self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)
        self._widget.sigHomeClicked.connect(self.home)
        # absolute movement
        self._widget.sigStepAbsoluteClicked.connect(self.moveAbsolute)
        # trigIO params
        self._widget.sigsetIOparams1DropDown.connect(self.set_IO_params) 
        self._widget.sigsetIOparams2DropDown.connect(self.set_IO_params)
        # relative movement setting io channel 1
        self._widget.sigsetRelDistanceClicked.connect(self.set_relative_distance)

        # update initial positions
        for pName, pManager in self._master.positionersManager:
            print(dir(pManager))
            for axis in pManager.axes:  
                print(axis)  
                initialPos = pManager._initialPosition
                self._widget.updatePosition(pName, axis, initialPos)
                    

    def closeEvent(self):                               
        self.__logger.debug('Closing PositionerController, but not doing anything.')

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def getSpeed(self):
        return self._master.positionersManager.execOnAll(lambda p: p.speed)
    
    def home(self, positionerName, axis):
        self._runInThread('home', positionerName, axis, None)

    def move(self, positionerName, axis, dist):
        self._runInThread('move', positionerName, axis, dist)

    def moveAbsolute(self, positionerName, axis):
        dist = self._widget.getAbsPosition(positionerName, axis)
        self._runInThread('moveAbsolute', positionerName, axis, dist)

    def setPos(self, positionerName, axis, position):
        self._runInThread('setPosition', positionerName, axis, position)

    def _runInThread(self, operation, positionerName, axis, dist):
        if self.thread_running:
            self.__logger.error(f"Thread is already running. Cannot execute {operation} command for {positionerName} on {axis} with distance {dist}")
            return

        self.thread_running = True
        positionerManager = self._master.positionersManager[positionerName]
        self.thread = QThread()
        self.worker = Worker(positionerManager, operation, axis, dist)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._onThreadFinished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.error.connect(self._handleWorkerError)
        self.worker.finished.connect(lambda: self.updatePosition(positionerName, axis))
        self.thread.start()

    def _onThreadFinished(self):
        self.thread_running = False
        self.thread.quit()
        self.thread.wait()  # Ensure the thread is finished before deleting

    def _handleWorkerError(self, errorMsg):
        self.__logger.error(f"Worker error: {errorMsg}")

    def stepUp(self, positionerName, axis):
        self.move(positionerName, axis, self._widget.getStepSize(positionerName, axis))

    def stepDown(self, positionerName, axis):
        self.move(positionerName, axis, -self._widget.getStepSize(positionerName, axis))

    def setSpeedGUI(self, axis):
        positionerName = self.getPositionerNames()[0]
        speed = self._widget.getSpeed()                                            # this line gets the input into the widget
        print('_________________getSpeed ', speed)
        self.setSpeed(positionerName=positionerName, axis=axis,speed=speed)
        self.updateSpeed(positionerName, axis)
    
    def updateSpeed(self, positionerName, axis):                                   # added this function to update the speed in the gui
        newSpeed = self._master.positionersManager[positionerName].speed(axis)
        print('_________________newSpeed ', newSpeed)
        self._widget.updateSpeed(positionerName, axis, newSpeed)
        self.setSharedAttr(positionerName, axis, _positionAttr, newSpeed)

    def setSpeed(self, positionerName, axis, speed=(1000,1000,1000)):
        self._master.positionersManager[positionerName].setSpeed(axis, speed)
        
    def updatePosition(self, positionerName, axis):
        newPos = self._master.positionersManager[positionerName].getPosition(axis) # changed this from ...[positionerName].position(axis) to ...[positionerName].getPosition(axis) 
        self._widget.updatePosition(positionerName, axis, newPos)                  # because .position[axis] just returns the initial position
        self.setSharedAttr(positionerName, axis, _positionAttr, newPos)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 4 or key[0] != _attrCategory:
            return

        positionerName = key[1]
        axis = key[2]
        if key[3] == _positionAttr:
            self.setPositioner(positionerName, axis, value)

    def setSharedAttr(self, positionerName, axis, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, positionerName, axis, attr)] = value
        finally:
            self.settingAttr = False

    def setXYPosition(self, x, y):
        positionerX = self.getPositionerNames()[0]
        positionerY = self.getPositionerNames()[1]
        self.__logger.debug(f"Move {positionerX}, axis X, dist {str(x)}")
        self.__logger.debug(f"Move {positionerY}, axis Y, dist {str(y)}")
        #self.move(positionerX, 'X', x)
        #self.move(positionerY, 'Y', y)

    def setZPosition(self, z):
        positionerZ = self.getPositionerNames()[2]
        self.__logger.debug(f"Move {positionerZ}, axis Z, dist {str(z)}")
        #self.move(self.getPositionerNames[2], 'Z', z)


    def set_IO_params(self, positionerName, axis):
        io_param1 = self._widget.getIOparams1(positionerName, axis)
        io_param2 = self._widget.getIOparams2(positionerName, axis)
        self._master.positionersManager[positionerName].set_triggerIOconfig([io_param1, io_param2])

    '''
    # trigger stuff
    def set_IO_params(self, positionerName, axis):
        io_params = self._widget.getIOparams(positionerName, axis)
        self.__logger.debug(f"Setting IO params for {positionerName}, axis {axis}, trig1_mode {io_params[0]}, trig2_mode {io_params[1]}, hardcoding polarity HIGH.")
        self._master.positionersManager[positionerName].set_triggerIOconfig(io_params)
    '''

    def set_relative_distance(self, positionerName, axis):
        rel_distance = self._widget.getRelDist(positionerName, axis)
        self.__logger.debug(f"Setting relative distance for {positionerName}, axis {axis}, relative distance {rel_distance}.")
        self._master.positionersManager[positionerName].set_rel_move_params(rel_distance)

    def updateRelDistance(self, positionerName, axis, rel_distance):
        self._widget.update_rel_distance(positionerName, axis, rel_distance)

    '''
    def moveAbsolute(self, positionerName, axis):
        """ Moves positioner by dist micrometers in the specified axis. ABSOLUTE MOVEMENT."""
        dist = self._widget.getAbsPosition(positionerName, axis)
        self._master.positionersManager[positionerName].moveAbsolute(dist, axis)
        # continuisly check the position
        while round(self._master.positionersManager[positionerName].getPosition(axis))!=dist:
            time.sleep(0.5)
            self.updatePosition(positionerName, axis)
    '''

    @APIExport()
    def getPositionerNames(self) -> List[str]:
        """ Returns the device names of all positioners. These device names can
        be passed to other positioner-related functions. """
        return self._master.positionersManager.getAllDeviceNames()

    @APIExport()
    def getPositionerPositions(self) -> Dict[str, Dict[str, float]]:
        """ Returns the positions of all positioners. """
        return self.getPos()

    @APIExport(runOnUIThread=True)
    def setPositionerStepSize(self, positionerName: str, stepSize: float) -> None:
        """ Sets the step size of the specified positioner to the specified
        number of micrometers. """
        self._widget.setStepSize(positionerName, stepSize)

    @APIExport(runOnUIThread=True)
    def movePositioner(self, positionerName: str, axis: str, dist: float) -> None:
        """ Moves the specified positioner axis by the specified number of
        micrometers. """
        self.move(positionerName, axis, dist)

    @APIExport(runOnUIThread=True)
    def setPositioner(self, positionerName: str, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(positionerName, axis, position)

    @APIExport(runOnUIThread=True)
    def setPositionerSpeed(self, positionerName: str, speed: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setSpeed(positionerName, speed)

    @APIExport(runOnUIThread=True)
    def setMotorsEnabled(self, positionerName: str, is_enabled: int) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self._master.positionersManager[positionerName].setEnabled(is_enabled)

    @APIExport(runOnUIThread=True)
    def stepPositionerUp(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in positive direction by its
        set step size. """
        self.stepUp(positionerName, axis)

    @APIExport(runOnUIThread=True)
    def stepPositionerDown(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in negative direction by its
        set step size. """
        self.stepDown(positionerName, axis)




_attrCategory = 'Positioner'
_positionAttr = 'Position'


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
