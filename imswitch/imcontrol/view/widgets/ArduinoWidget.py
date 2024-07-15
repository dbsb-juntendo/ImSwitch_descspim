from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget

class ArduinoWidget(Widget):
    ''' Widget to control the ELL9 slider through Arduino.'''

    sigHomeClicked = QtCore.Signal()                
    sigSetPosClicked = QtCore.Signal()           
    sigAddRowClicked = QtCore.Signal()     
    sigRemoveRowClicked = QtCore.Signal()
    sigSendToArduinoClicked = QtCore.Signal()  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.homeButton = guitools.BetterPushButton('Home')
        self.setPosLabel = QtWidgets.QLabel('Set Position (1-4): ')
        #TODO # at some point this should be the filter cube names
        self.setPosEdit = QtWidgets.QLineEdit('1')                      
        self.setPosButton = guitools.BetterPushButton('Set')

        self.addRowButton = guitools.BetterPushButton('+')
        self.removeRowButton = guitools.BetterPushButton('-')
        self.sendToArduino = guitools.BetterPushButton('Send')

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.homeButton, 0, 0)
        self.grid.addWidget(self.setPosLabel, 0, 1)
        self.grid.addWidget(self.setPosEdit, 0, 2)
        self.grid.addWidget(self.setPosButton, 0, 3)
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.grid.addWidget(line, 1, 0, 1, 4)

        # add table for the channel selection
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Channel', 'Filter', 'Laser'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.grid.addWidget(self.tableWidget, 2, 0, 3, 3)
        self.filterOptions = ["Filter 1", "Filter 2", "Filter 3"]
        self.laserOptions = ["2", "8"]                             #TODO this should be the lasers: 488 - ttl line 8, 594 - ttl line 2
        self.grid.addWidget(self.addRowButton, 2, 3)
        self.grid.addWidget(self.removeRowButton, 3, 3)
        self.grid.addWidget(self.sendToArduino, 4, 3)

        # connect the buttons
        self.homeButton.clicked.connect(self.sigHomeClicked)
        self.setPosButton.clicked.connect(self.sigSetPosClicked)
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

        # Filter column with dropdown menu
        filterCombo = QtWidgets.QComboBox()
        filterCombo.addItems(self.filterOptions)
        self.tableWidget.setCellWidget(rowCount, 1, filterCombo)

        # Laser column with dropdown menu
        laserCombo = QtWidgets.QComboBox()
        laserCombo.addItems(self.laserOptions)
        self.tableWidget.setCellWidget(rowCount, 2, laserCombo)

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
    
'''
{
  "detectors": {
    "thorlabscam": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ThorCamSciManager",
      "managerProperties": {
        "cameraListIndex": 0,
        "thorcamsci": {
          "exposure": 50,
          "gain": 0,
          "blacklevel": 100,
          "operation_mode": 0
          }
      },
      "forAcquisition": true
    }
  },
  "arduino":{
    "port": "COM3",
    "baudrate": 9600
  },
  "availableWidgets": [
    "Settings",
    "View",
    "Recording",
    "Image",
    "Arduino"
    ]
}
'''