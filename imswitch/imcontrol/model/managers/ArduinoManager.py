from imswitch.imcommon.model import initLogger
from abc import ABC
import serial

class ArduinoManager(ABC):
    def __init__(self, ArduinoInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        if ArduinoInfo is None:
            return
        self.__ArduinoInfo = ArduinoInfo
        self.__port = self.__ArduinoInfo.port
        self.__baudrate = self.__ArduinoInfo.baudrate
        # initialise
        try:
            self.arduino = serial.Serial(self.__port, self.__baudrate)
            self.__logger.debug(f'Initialized Arduino.')

        except:
            self.__logger.error(f'Failed to initialize Arduino on port {self.__port}.')

    def home(self):
        self.__logger.debug(f'Homing ELL9.')
        self.arduino.write(b'0\n')

    def moveToPos(self, pos:int):
        self.__logger.debug(f'Moving ELL9 to Position {pos}.')
        self.arduino.write(f'{pos}\n'.encode())

    def sendToArd(self, tableData):
        self.__logger.debug(f'Sending data to Arduino.')
        toSend = ''
        for row in tableData:
            filter = row[1][-1]
            laser = row[2][-1]
            toSend += f'{filter}{laser}\n'
        self.arduino.write(toSend.encode())

    def startScan(self):
        self.__logger.debug(f'Starting scan.')
        self.arduino.write(b's\n')

'''
import serial
import time

# Configure the serial port
ser = serial.Serial('COM3', 9600)  # Update with your Arduino's COM port

def move_stage(target_position):
    ser.write(f"{target_position}\n".encode())
    print(f"Moving stage to position {target_position}")
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(response)
            if response == "Movement complete.":
                break

try:
    while True:
        target = int(input("Enter the target position (1 to 4) or q to quit: "))
        
        if target in [1, 2, 3, 4]:
            move_stage(target)
        elif target.lower() == 'q':
            break
        else:
            print("Invalid input. Please enter a number from 1 to 4 or q to quit.")
except KeyboardInterrupt:
    pass
finally:
    ser.close()
'''