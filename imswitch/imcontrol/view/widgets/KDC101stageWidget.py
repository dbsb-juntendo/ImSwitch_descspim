from qtpy import QtCore, QtGui, QtWidgets
from .basewidgets import Widget
from imswitch.imcontrol.view import guitools
from imswitch.imcontrol.view.widgets.PositionerWidget import PositionerWidget

#TODO not working yet

class KDC101stageWidget(Widget):
    """ Widget for controlling the KDC101 stage."""

    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal(str, str)  # (positionerName, axis)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('XXXXXXXXXXXXXX________________load KDC101stageWidget')
        self.setWindowTitle('Setup status')

        """GUI elements"""

        '''
        self.illuminationLabel = QtWidgets.QLabel('Current illumination config:')
        self.illuminationLabel.setFont(QtGui.QFont('Calibri', 14))
        self.illuminationLabel.setStyleSheet("font-weight: bold")
        self.illuminationStatusLabel = QtWidgets.QLabel('')
        self.illuminationStatusLabel.setFont(QtGui.QFont('Calibri', 14))
        self.illuminationStatusLabel.setStyleSheet("font-weight: bold")
        self.detectionLabel = QtWidgets.QLabel('Current detection config:')
        self.detectionLabel.setFont(QtGui.QFont('Calibri', 14))
        self.detectionLabel.setStyleSheet("font-weight: bold")
        self.detectionStatusLabel = QtWidgets.QLabel('')
        self.detectionStatusLabel.setFont(QtGui.QFont('Calibri', 14))
        self.detectionStatusLabel.setStyleSheet("font-weight: bold")

        """Rotation stage"""
        self.rotationStageHeader = QtWidgets.QLabel('Rotation stage')
        self.rotationStageHeader.setFont(QtGui.QFont('Calibri', 14))
        self.rotationStageHeader.setStyleSheet("font-weight: bold")

        self.rotationStagePosLabel = QtWidgets.QLabel('Set position (deg) of rotation stage')
        self.rotationStagePosEdit = guitools.BetterDoubleSpinBox()
        self.rotationStagePosEdit.setDecimals(4)
        self.rotationStagePosEdit.setMinimum(-360)
        self.rotationStagePosEdit.setMaximum(360)
        self.rotationStagePosEdit.setSingleStep(0.01)
        self.jogStepSizeLabel = QtWidgets.QLabel('Set jog step size (deg)')
        self.jogStepSizeEdit = guitools.BetterDoubleSpinBox()
        self.jogStepSizeEdit.setDecimals(4)
        self.jogStepSizeEdit.setMaximum(360)
        self.jogStepSizeEdit.setSingleStep(0.01)
        self.jogPositiveButton = guitools.BetterPushButton('>>')
        self.jogNegativeButton = guitools.BetterPushButton('<<')
        self.currentPosOfRotationStageLabel = QtWidgets.QLabel('Current position (deg) of rotation stage')
        self.currentPosOfRotationStageDisp = QtWidgets.QLabel('')

        '''