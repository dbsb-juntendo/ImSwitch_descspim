from ..basecontrollers import ImConWidgetController

class ArduinoController(ImConWidgetController):
    '''Linked to ArduinoWidget.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # connect the buttons
        self._widget.sigHomeClicked.connect(self.home)
        self._widget.sigSetPosClicked.connect(self.moveToPos)
        self._widget.sigAddRowClicked.connect(self.addRow)
        self._widget.sigRemoveRowClicked.connect(self.removeRow)
        self._widget.sigSendToArduinoClicked.connect(self.sendTableDataToArduino)

    def home(self):
        self._master.arduinoManager.home()
    
    def moveToPos(self):
        new_pos = self._widget.getPos()
        if new_pos not in range(1, 5):
            self._logger.error('Invalid position. Must be between 1 and 4.')
        else:
            self._master.arduinoManager.moveToPos(new_pos)
    
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
                filter_selected = filter_combo.currentText()
                laser_selected = laser_combo.currentText()
                table_data.append((channel, filter_selected, laser_selected))


        self._logger.debug(f'Table data: {table_data}')
        self._master.arduinoManager.sendToArd(table_data)