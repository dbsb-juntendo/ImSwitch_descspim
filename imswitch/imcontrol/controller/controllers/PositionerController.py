from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class PositionerController(ImConWidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            #hasSpeed = hasattr(pManager, 'speed')
            #TODO homing
            #TODO stopping
            self._widget.addPositioner(pName, pManager.axes)#, hasSpeed) #TODO homing, stopping
            for axis in pManager.axes:
                                                           # on this KDC101 stage is only one axis
                self.setSharedAttr(pName, axis, _positionAttr, pManager.position[axis])
                #if hasSpeed:
                #    if pManager.speed[axis]== 0:
                #        mSpeed = 10000
                #    else:
                #        mSpeed = pManager.speed[axis]       # get the speed in um/s
                #    self.setSharedAttr(pName, axis, _speedAttr, mSpeed)
                #TODO homing
                #TODO stopping

        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        #self._commChannel.sigUpdateMotorPosition.connect(self.updateAllPositionGUI) # force update position in GUI
        #self._commChannel.sigSetSpeed.connect(self.updateAllSpeedGUI) # force update speed in GUI
        #self._commChannel.sigSetSpeed.connect(lambda speed: self.setSpeedGUI(speed))

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(self.stepUp)
        self._widget.sigStepDownClicked.connect(self.stepDown)
        self._widget.sigStepAbsoluteClicked.connect(self.moveAbsolute)   
        #self._widget.sigsetSpeedClicked.connect(self.setSpeedGUI)

        #TODO homing
        #TODO stopping     

    def closeEvent(self):
        self._master.positionersManager.execOnAll(
            lambda p: [p.setPosition(0, axis) for axis in p.axes],
            condition = lambda p: p.resetOnClose
        )

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    #def getSpeed(self):
    #    return self._master.positionersManager.execOnAll(lambda p: p.speed)

    def move(self, positionerName, axis, dist, is_absolute=False):
        """ Moves positioner by dist micrometers in the specified axis. """
        if is_absolute:
            self._master.positionersManager[positionerName].setPosition(dist, axis)
        else:
            self._master.positionersManager[positionerName].move(dist, axis)
        self._commChannel.sigUpdateMotorPosition.emit()            # dont know what this does
        self.updatePosition(positionerName, axis)

    def setPos(self, positionerName, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        self._master.positionersManager[positionerName].setPosition(position, axis)
        self.updatePosition(positionerName, axis)

    def moveAbsolute(self, positionerName, axis):
        print('_________________moveAbsolute ', self._widget.getAbsPosition(positionerName, axis))
        self.move(positionerName, axis, self._widget.getAbsPosition(positionerName, axis), is_absolute=True)

    def stepUp(self, positionerName, axis):
        self.move(positionerName, axis, self._widget.getStepSize(positionerName, axis))

    def stepDown(self, positionerName, axis):
        self.move(positionerName, axis, -self._widget.getStepSize(positionerName, axis))

    #def setSpeed(self, positionerName, axis, speed=(1000,1000,1000)):
    #    self._master.positionersManager[positionerName].setSpeed(speed, axis)
    #    self.setSharedAttr(positionerName, axis, _speedAttr, speed)
    #    self._widget.setSpeedSize(positionerName, axis, speed)

    #def updateAllSpeedGUI(self):
    #    # update all speeds for all axes in GUI
    #    for positionerName in self._master.positionersManager.getAllDeviceNames():
    #        for axis in self._master.positionersManager[positionerName].axes:
    #            self.updateSpeed(positionerName, axis)

    #def setSpeedGUI(self, axis=None):
    #    positionerName = self.getPositionerNames()[0]
    #    speed = self._widget.getSpeed(positionerName, axis)                                            # this line gets the input into the widget
    #    self.setSpeed(positionerName=positionerName, axis=axis,speed=speed)
    #    self.updateSpeed(positionerName, axis)

    def updateAllPositionGUI(self):
        # update all positions for all axes in GUI
        for positionerName in self._master.positionersManager.getAllDeviceNames():
            for axis in self._master.positionersManager[positionerName].axes:
                self.updatePosition(positionerName, axis)
                self.updateSpeed(positionerName, axis)

    def updatePosition(self, positionerName, axis):
        newPos = self._master.positionersManager[positionerName].getPosition(axis) # changed this from ...[positionerName].position(axis) to ...[positionerName].getPosition(axis) 
        self._widget.updatePosition(positionerName, axis, newPos)                  # because .position[axis] just returns the initial position
        self.setSharedAttr(positionerName, axis, _positionAttr, newPos)

    #def updateSpeed(self, positionerName, axis):
    #    newSpeed = self._master.positionersManager[positionerName].speed[axis]
    #    self._widget.updateSpeed(positionerName, axis, newSpeed)
    #    self.setSharedAttr(positionerName, axis, _speedAttr, newSpeed)

    #TODO homing
    #TODO stopping

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
        print('_____________apiexport step up')
        self.stepUp(positionerName, axis)

    @APIExport(runOnUIThread=True)
    def stepPositionerDown(self, positionerName: str, axis: str) -> None:
        """ Moves the specified positioner axis in negative direction by its
        set step size. """
        self.stepDown(positionerName, axis)




_attrCategory = 'Positioner'
_positionAttr = 'Position'
#_speedAttr = "Speed"
#TODO homing
#TODO stopping


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
