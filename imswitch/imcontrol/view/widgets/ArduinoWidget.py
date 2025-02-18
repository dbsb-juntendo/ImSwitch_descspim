from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget

class ArduinoWidget(Widget):
    ''' Widget to control the ELL9 slider through Arduino.'''

    sigHomeClicked = QtCore.Signal()                
    sigSetPos1Clicked = QtCore.Signal()
    sigSetPos2Clicked = QtCore.Signal()
    sigSetPos3Clicked = QtCore.Signal()
    sigSetPos4Clicked = QtCore.Signal()           
    sigAddRowClicked = QtCore.Signal()     
    sigRemoveRowClicked = QtCore.Signal()
    sigSendToArduinoClicked = QtCore.Signal()  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.homeButton = guitools.BetterPushButton('Home')
        self.pos1button = guitools.BetterPushButton('Pos: 1')
        self.pos2button = guitools.BetterPushButton('Pos: 2')
        self.pos3button = guitools.BetterPushButton('Pos: 3')
        self.pos4button = guitools.BetterPushButton('Pos: 4')

        self.addRowButton = guitools.BetterPushButton('+')
        self.removeRowButton = guitools.BetterPushButton('-')
        self.sendToArduino = guitools.BetterPushButton('Send')

        self.lastSentCommand = QtWidgets.QLabel('Last: 00')

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.homeButton, 0, 0)
        self.grid.addWidget(self.pos1button, 0, 1)
        self.grid.addWidget(self.pos2button, 0, 2)
        self.grid.addWidget(self.pos3button, 0, 3)
        self.grid.addWidget(self.pos4button, 0, 4)
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.grid.addWidget(line, 1, 0, 1, 5)

        # add table for the channel selection
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Channel', 'Laser', 'Filter'])  
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.grid.addWidget(self.tableWidget, 2, 0, 4, 4)
        self.laserOptions = ["0"]  
        self.filterOptions = ["Filter 1", "Filter 2", "Filter 3", "Filter 4"]                          
        self.grid.addWidget(self.addRowButton, 2, 4)
        self.grid.addWidget(self.removeRowButton, 3, 4)
        self.grid.addWidget(self.sendToArduino, 4, 4)

        self.grid.addWidget(self.lastSentCommand, 5, 4)

        # connect the buttons
        self.homeButton.clicked.connect(self.sigHomeClicked)
        self.pos1button.clicked.connect(self.sigSetPos1Clicked)
        self.pos2button.clicked.connect(self.sigSetPos2Clicked)
        self.pos3button.clicked.connect(self.sigSetPos3Clicked)
        self.pos4button.clicked.connect(self.sigSetPos4Clicked)

        self.addRowButton.clicked.connect(self.sigAddRowClicked)
        self.removeRowButton.clicked.connect(self.sigRemoveRowClicked)
        self.sendToArduino.clicked.connect(self.sigSendToArduinoClicked)
        self.channelCounter = 1


    def addTableRow(self):
        rowCount = self.tableWidget.rowCount()

        # Insert new row
        self.tableWidget.insertRow(rowCount)

        # Channel column
        channelItem = QtWidgets.QTableWidgetItem(f"Channel {self.channelCounter}")
        self.tableWidget.setItem(rowCount, 0, channelItem)

        # Laser column with dropdown menu
        laserCombo = QtWidgets.QComboBox()
        laserCombo.addItems(self.laserOptions)
        self.tableWidget.setCellWidget(rowCount, 1, laserCombo)

        # Filter column with dropdown menu
        filterCombo = QtWidgets.QComboBox()
        filterCombo.addItems(self.filterOptions)
        self.tableWidget.setCellWidget(rowCount, 2, filterCombo)

        # Increment channel counter for next row
        self.channelCounter += 1

    def removeSelectedRow(self):
        current_row = self.tableWidget.currentRow()
        if current_row >= 0:
            self.tableWidget.removeRow(current_row)
            self.channelCounter -= 1

    def setPos(self, pos):
        self.setPosEdit.setText(str(pos))
    
    def getPos(self):
        return int(self.setPosEdit.text())
    
    def updateLastCommand(self, command):
        self.lastSentCommand.setText(f'Last: {command}')
    
    def updateLaserOptions(self, options):
        self.laserOptions = options

    def updateEmissionFilterOptions(self, options):
        self.filterOptions = [f'{i} - {options[i]}' for i in options]

    def updateSliderLabels(self, options):
        print(options)
        self.pos1button = guitools.BetterPushButton(f'1 - {options["1"]}')
        self.pos2button = guitools.BetterPushButton(f'2 - {options["2"]}')
        self.pos3button = guitools.BetterPushButton(f'3 - {options["3"]}')
        self.pos4button = guitools.BetterPushButton(f'4 - {options["4"]}')