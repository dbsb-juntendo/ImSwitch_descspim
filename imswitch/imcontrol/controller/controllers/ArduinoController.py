from ..basecontrollers import ImConWidgetController

class ArduinoController(ImConWidgetController):
    '''Linked to ArduinoWidget.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.laserTTLs = [(lManager.wavelength, lManager._ttlLine.split('TTL')[-1]) for lName, lManager in self._master.lasersManager]
        print(dir(self._master.arduinoManager))
        self.emissionFilters = self._master.arduinoManager._ArduinoManager__emissionFilters
        
        # connect the buttons
        self._widget.sigHomeClicked.connect(self.home)
        self._widget.sigSetPos1Clicked.connect(self.moveToPos1)
        self._widget.sigSetPos2Clicked.connect(self.moveToPos2)
        self._widget.sigSetPos3Clicked.connect(self.moveToPos3)
        self._widget.sigSetPos4Clicked.connect(self.moveToPos4)

        self._widget.sigAddRowClicked.connect(self.addRow)
        self._widget.sigRemoveRowClicked.connect(self.removeRow)
        self._widget.sigSendToArduinoClicked.connect(self.sendTableDataToArduino)

        # update laser ttls
        self._widget.updateLaserOptions([f'{l[0]} - TTL {l[1]}' for l in self.laserTTLs])
        self._widget.updateEmissionFilterOptions(self.emissionFilters)
        self._widget.updateSliderLabels(self.emissionFilters)
        
    def home(self):
        self._master.arduinoManager.home()
    
    def moveToPos(self, pos):
        if pos not in range(1, 5):
            self._logger.error('Invalid position. Must be between 1 and 4.')
        else:
            self._master.arduinoManager.moveToPos(pos)
    
    def updateLastCommand(self, command):
        self._widget.updateLastCommand(command)

    def moveToPos1(self):
        self.moveToPos(1)
    
    def moveToPos2(self):
        self.moveToPos(2)
    
    def moveToPos3(self):
        self.moveToPos(3)
    
    def moveToPos4(self):
        self.moveToPos(4)

    def addRow(self):
        self._widget.addTableRow()
    
    def removeRow(self):
        self._widget.removeSelectedRow()
    
    def sendTableDataToArduino(self):
        table_data = []
        table_widget = self._widget.tableWidget
        num_rows = table_widget.rowCount()

        for row in range(num_rows):
            channel_item = table_widget.item(row, 0)
            filter_combo = table_widget.cellWidget(row, 1)
            laser_combo = table_widget.cellWidget(row, 2)

            if channel_item is not None and filter_combo is not None and laser_combo is not None:
                channel = channel_item.text()
                filter_selected = filter_combo.currentText()[0]
                print(filter_selected)
                laser_selected = laser_combo.currentText().split()[-1]
                table_data.append((channel, filter_selected, laser_selected))

        toSend = ''
        for row in table_data:
            filter = row[1][-1]
            laser = row[2][-1]
            toSend += f'{filter}{laser}'
        self._logger.debug(f'Table data: {toSend}')
        self._master.arduinoManager.sendToArd(toSend)
        self.updateLastCommand(toSend)