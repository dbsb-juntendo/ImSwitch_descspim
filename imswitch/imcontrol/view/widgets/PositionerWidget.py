from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezo movement. """

    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepAbsoluteClicked = QtCore.Signal(str, str)  # (positionerName, axis) for absolute movement
    #sigsetSpeedClicked = QtCore.Signal()  # (speed)
    sigHomeClicked = QtCore.Signal(str, str)  # (positionerName)

    #sigsetIOparams1Clicked = QtCore.Signal(str, str)  # (io_params)
    sigsetRelDistanceClicked = QtCore.Signal(str, str)  # (rel_distance)
    sigSetIOparamsClicked = QtCore.Signal(str, str)  # (io_params)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName, axes, speed):
        for i in range(len(axes)):
            axis = axes[i]
            parNameSuffix = self._getParNameSuffix(positionerName, axis)
            label = f'{positionerName} -- {axis}' if positionerName != axis else positionerName

            self.pars['Label' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{label}</strong>')
            self.pars['Label' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['Position' + parNameSuffix] = QtWidgets.QLabel(f'<strong>{0:.4f} µm</strong>')
            self.pars['Position' + parNameSuffix].setTextFormat(QtCore.Qt.RichText)
            self.pars['UpButton' + parNameSuffix] = guitools.BetterPushButton('+')
            self.pars['DownButton' + parNameSuffix] = guitools.BetterPushButton('-')
            self.pars['StepEdit' + parNameSuffix] = QtWidgets.QLineEdit('5')
            self.pars['StepUnit' + parNameSuffix] = QtWidgets.QLabel(' µm')
            self.pars['HomeButton' + parNameSuffix] = guitools.BetterPushButton('Home')

            # add absolute movement
            self.pars['AbsolutePosEdit' + parNameSuffix] = QtWidgets.QLineEdit('0')             
            self.pars['AbsolutePosButton' + parNameSuffix] = guitools.BetterPushButton('Go!')
            
            # trigger modes 
            self.pars['trig1_mode' + parNameSuffix] = QtWidgets.QLineEdit('0')                  #TODO change to initial
            #self.pars['set_trig1_mode' + parNameSuffix] = guitools.BetterPushButton('SET')
            self.pars['rel_distance1' + parNameSuffix] = QtWidgets.QLineEdit('0')               #TODO change to initial
            self.pars['rel_distance1_unit' + parNameSuffix] = QtWidgets.QLabel(' µm')
            self.pars['set_rel_distance1' + parNameSuffix] = guitools.BetterPushButton('SET')

            self.pars['trig2_mode' + parNameSuffix] = QtWidgets.QLineEdit('0')                  #TODO change to initial
            self.pars['set_trig2_mode' + parNameSuffix] = guitools.BetterPushButton('SET')
            #self.pars['rel_distance2' + parNameSuffix] = QtWidgets.QLineEdit('0')
            #self.pars['rel_distance2_unit' + parNameSuffix] = QtWidgets.QLabel(' µm')

            # row 1
            self.grid.addWidget(self.pars['Label' + parNameSuffix], 3*self.numPositioners, 0)
            self.grid.addWidget(self.pars['Position' + parNameSuffix], 3*self.numPositioners, 1)
            self.grid.addWidget(self.pars['UpButton' + parNameSuffix], 3*self.numPositioners, 2)
            self.grid.addWidget(self.pars['DownButton' + parNameSuffix], 3*self.numPositioners, 3)
            self.grid.addWidget(QtWidgets.QLabel('Step'), 3*self.numPositioners, 4)
            self.grid.addWidget(self.pars['StepEdit' + parNameSuffix], 3*self.numPositioners, 5)
            self.grid.addWidget(self.pars['StepUnit' + parNameSuffix], 3*self.numPositioners, 6)
            self.grid.addWidget(self.pars['HomeButton' + parNameSuffix], 3*self.numPositioners, 7)
            # row 2
            self.grid.addWidget(QtWidgets.QLabel('Abs: '), 3*self.numPositioners+1, 0)
            self.grid.addWidget(self.pars['AbsolutePosEdit' + parNameSuffix], 3*self.numPositioners+1, 1)
            self.grid.addWidget(self.pars['AbsolutePosButton' + parNameSuffix], 3*self.numPositioners+1, 2)

            # row 3
            self.grid.addWidget(QtWidgets.QLabel('IO1_mode: '), 3*self.numPositioners+2, 0)
            self.grid.addWidget(self.pars['trig1_mode' + parNameSuffix], 3*self.numPositioners+2, 1)
            #self.grid.addWidget(self.pars['set_trig1_mode' + parNameSuffix], 2*self.numPositioners+2, 2)
            self.grid.addWidget(QtWidgets.QLabel('Rel IO1 move: '), 3*self.numPositioners+2, 2)
            self.grid.addWidget(self.pars['rel_distance1' + parNameSuffix], 3*self.numPositioners+2, 3)
            self.grid.addWidget(self.pars['rel_distance1_unit' + parNameSuffix], 3*self.numPositioners+2, 4)
            self.grid.addWidget(self.pars['set_rel_distance1' + parNameSuffix], 3*self.numPositioners+2, 5)
            self.grid.addWidget(QtWidgets.QLabel('IO2_mode: '), 3*self.numPositioners+2, 6)
            self.grid.addWidget(self.pars['trig2_mode' + parNameSuffix], 3*self.numPositioners+2, 7)
            self.grid.addWidget(self.pars['set_trig2_mode' + parNameSuffix], 3*self.numPositioners+2, 8)

            # Connect signals
            self.pars['UpButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepUpClicked.emit(positionerName, axis)
            )
            self.pars['DownButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepDownClicked.emit(positionerName, axis)
            )
            self.pars['HomeButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigHomeClicked.emit(positionerName, axis)
            )

            # absolute movement button
            self.pars['AbsolutePosButton' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigStepAbsoluteClicked.emit(positionerName, axis)
            )
            
            # set button trig1
            #self.pars['set_trig1_mode' + parNameSuffix].clicked.connect(
            #    lambda *args, axis=axis: self.sigsetIOparams1Clicked.emit(positionerName, axis)
            #)
            # set button relmove 1
            self.pars['set_rel_distance1' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigsetRelDistanceClicked.emit(positionerName, axis)
            )
            # set button trig2
            self.pars['set_trig2_mode' + parNameSuffix].clicked.connect(
                lambda *args, axis=axis: self.sigSetIOparamsClicked.emit(positionerName, axis)
            )

            if speed:
                self.pars['Speed'] = QtWidgets.QLabel(f'<strong>{0:.2f} µm/s</strong>')
                self.pars['Speed'].setTextFormat(QtCore.Qt.RichText)
                self.pars['ButtonSpeedEnter'] = guitools.BetterPushButton('Enter')
                self.pars['SpeedEdit'] = QtWidgets.QLineEdit('1000')
                self.pars['SpeedUnit'] = QtWidgets.QLabel(' µm/s')
                self.grid.addWidget(self.pars['SpeedEdit'], 2*self.numPositioners, 10)
                self.grid.addWidget(self.pars['SpeedUnit'], 2*self.numPositioners, 11)
                self.grid.addWidget(self.pars['ButtonSpeedEnter'], 2*self.numPositioners, 12)
                self.grid.addWidget(self.pars['Speed'], 2*self.numPositioners, 7)


                self.pars['ButtonSpeedEnter'].clicked.connect(
                    lambda *args: self.sigsetSpeedClicked.emit()
                )
            self.numPositioners += 1
    
    # absolute movement
    def getAbsPosition(self, positionerName, axis):
        """ Returns the absolute position of the  specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['AbsolutePosEdit' + parNameSuffix].text())

    def getStepSize(self, positionerName, axis):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['StepEdit' + parNameSuffix].text())

    def setStepSize(self, positionerName, axis, stepSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['StepEdit' + parNameSuffix].setText(stepSize)
        print('When is this run')

    def getSpeed(self):
        """ Returns the step size of the specified positioner axis in
        micrometers. """
        return float(self.pars['SpeedEdit'].text())

    def setSpeedSize(self, positionerName, axis, speedSize):
        """ Sets the step size of the specified positioner axis to the
        specified number of micrometers. """
        self.pars['SpeedEdit'].setText(speedSize)

    def updatePosition(self, positionerName, axis, position):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Position' + parNameSuffix].setText(f'<strong>{position:.4f} µm</strong>')

    def updateSpeed(self, positionerName, axis, speed):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['Speed' + parNameSuffix].setText(f'<strong>{speed:.2f} µm/s</strong>')
    
    # trigger stuff
    def getIOparams(self, positionerName, axis):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return (int(self.pars['trig1_mode' + parNameSuffix].text()), int(self.pars['trig2_mode' + parNameSuffix].text()))
    
    def getRelDist(self, positionerName, axis):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        return float(self.pars['rel_distance1' + parNameSuffix].text())

    def update_rel_distance(self, positionerName, axis, rel_distance):
        parNameSuffix = self._getParNameSuffix(positionerName, axis)
        self.pars['rel_distance1' + parNameSuffix].setText(str(rel_distance))        # maybe not correct like this, can you set text in a line edit?

    def _getParNameSuffix(self, positionerName, axis):
        return f'{positionerName}--{axis}'


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
