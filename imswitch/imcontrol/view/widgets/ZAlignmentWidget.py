from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import naparitools
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class ZAlignmentWidget(Widget):
    """ Widget for calculating the relative movement factor between the sample and camera stage."""

    # buttons
    sigSavePosOneClicked = QtCore.Signal()      
    sigSavePosTwoClicked = QtCore.Signal()  
    sigZstepSetClicked = QtCore.Signal()    
    sigCalculateClicked = QtCore.Signal()
    sigMovePosOneClicked = QtCore.Signal()
    sigMovePosTwoClicked = QtCore.Signal()
    sigUpdateStagesClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.saveposOneButton = guitools.BetterPushButton('Save Position 1')
        self.saveposTwoButton = guitools.BetterPushButton('Save Position 2')

        self.zstepLabel = QtWidgets.QLabel('Z-Step: ').setTextFormat(QtCore.Qt.RichText)
        self.zstepEdit = QtWidgets.QLineEdit('1.0')
        self.zstepUnit = QtWidgets.QLabel(' µm').setTextFormat(QtCore.Qt.RichText)
        self.zstepSetButton = guitools.BetterPushButton('Set')

        self.pos1s = QtWidgets.QLabel(f'<strong>Sample: {0:.4f} µm</strong>')      # pos 1 camera stage
        self.pos1s.setTextFormat(QtCore.Qt.RichText)  
        self.pos1c = QtWidgets.QLabel(f'<strong>Camera: {0:.4f} µm</strong>')       # pos 1 sample stage
        self.pos1c.setTextFormat(QtCore.Qt.RichText)
        self.pos2c = QtWidgets.QLabel(f'<strong>Sample: {0:.4f} µm</strong>')
        self.pos2c.setTextFormat(QtCore.Qt.RichText)        # pos 2 camera stage
        self.pos2s = QtWidgets.QLabel(f'<strong>Camera: {0:.4f} µm</strong>')       # pos 2 sample stage
        self.pos2s.setTextFormat(QtCore.Qt.RichText)
        self.calculateButton = guitools.BetterPushButton('Calculate')

        # Results box
        self.factor = QtWidgets.QLabel(f'<strong>Factor: {0:.4f}</strong>')
        self.sampleZstep = QtWidgets.QLabel(f'<strong>Sample z-Step: {0:.4f} µm</strong>')
        self.cameraZstep = QtWidgets.QLabel(f'<strong>Camera z-Step: {0:.4f} µm</strong>')
        
        self.movePos1Button = guitools.BetterPushButton('Move to Pos 1')
        self.movePos2Button = guitools.BetterPushButton('Move to Pos 2')
        self.updateStagesButton = guitools.BetterPushButton('Update Stages')


        # add items to GridLayout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.saveposOneButton, 0, 0)
        self.grid.addWidget(self.saveposTwoButton, 0, 1)
        self.grid.addWidget(self.zstepLabel, 0, 2)
        self.grid.addWidget(self.zstepEdit, 0, 3)
        self.grid.addWidget(self.zstepUnit, 0, 4)
        self.grid.addWidget(self.zstepSetButton, 0, 5)

        self.grid.addWidget(self.pos1s, 1, 0)
        self.grid.addWidget(self.pos2s, 1, 1)
        self.grid.addWidget(self.pos1c, 2, 0)
        self.grid.addWidget(self.pos2c, 2, 1)

        self.grid.addWidget(self.calculateButton, 1, 2, 2, 4)

        # results box
        self.resultsGroup = QtWidgets.QGroupBox('Results')
        self.resultsLayout = QtWidgets.QGridLayout()
        self.resultsLayout.addWidget(self.factor, 0, 0)
        self.resultsLayout.addWidget(self.sampleZstep, 0, 1)
        self.resultsLayout.addWidget(self.cameraZstep, 0, 2)       
        self.resultsGroup.setLayout(self.resultsLayout) # at the end or at the beginning of each group?

        self.grid.addWidget(self.resultsGroup, 3, 0, 1, 5)

        self.grid.addWidget(self.movePos1Button, 4, 0)
        self.grid.addWidget(self.movePos2Button, 4, 1)
        self.grid.addWidget(self.updateStagesButton, 4, 2, 1, 4)
        # ...

        # connect the buttons
        self.saveposOneButton.clicked.connect(self.sigSavePosOneClicked)
        self.saveposTwoButton.clicked.connect(self.sigSavePosTwoClicked)
        self.zstepSetButton.clicked.connect(self.sigZstepSetClicked)
        self.calculateButton.clicked.connect(self.sigCalculateClicked)
        self.movePos1Button.clicked.connect(self.sigMovePosOneClicked)
        self.movePos2Button.clicked.connect(self.sigMovePosTwoClicked)
        self.updateStagesButton.clicked.connect(self.sigUpdateStagesClicked)
    
    # functions
    def update_pos1(self, sample_pos, camera_pos):
        """ Update the position of the camera and sample stage. """
        self.pos1s.setText(f'<strong>Sample: {sample_pos:.4f} µm</strong>')
        self.pos1c.setText(f'<strong>Camera: {camera_pos:.4f} µm</strong>')
    
    def update_pos2(self, sample_pos, camera_pos):
        """ Update the position of the camera and sample stage. """
        self.pos2s.setText(f'<strong>Sample: {sample_pos:.4f} µm</strong>')
        self.pos2c.setText(f'<strong>Camera: {camera_pos:.4f} µm</strong>')
    
    def getZstep(self):
        """ Get the z-step from the input field. """
        return float(self.zstepEdit.text())
    
    def getPositions(self):
        """ Get positions 1 and 2 of the camera and sample stage. """
        return (self.pos1s.text(), self.pos1c.text(), self.pos2s.text(), self.pos2c.text())
    
    def updateResults(self, factor, sampleZstep, cameraZstep):
        """ Update the results box with the calculated values. """
        self.factor.setText(f'<strong>Factor: {factor:.4f}</strong>')
        self.sampleZstep.setText(f'<strong>Sample z-Step: {sampleZstep:.4f} µm</strong>')
        self.cameraZstep.setText(f'<strong>Camera z-Step: {cameraZstep:.4f} µm</strong>')

    def getResultZstep(self):
        """ Get the z-step from the results box. """
        return (
            float(self.sampleZstep.text().split(' ')[2]),
            float(self.cameraZstep.text().split(' ')[2])
        )
