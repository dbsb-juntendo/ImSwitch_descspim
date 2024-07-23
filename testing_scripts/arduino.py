import serial
import time

def send_command(ser, command):
    ser.write(command.encode('utf-8'))
    #ser.write(b'')  # Send newline to signify end of command
    time.sleep(0.1)  # Wait for the Arduino to process the command

def read_response(ser):
    while ser.in_waiting > 0:
        response = ser.readline().decode('utf-8').strip()
        print("Arduino response:", response)

def main():
    # Open the serial connection (replace 'COM3' with your port)
    ser = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)  # Wait for the connection to initialize

    print("Interactive terminal. Type your commands below:")
    
    try:
        while True:
            user_input = input(">> ")
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting interactive terminal.")
                break
            
            send_command(ser, user_input)
            time.sleep(0.1)  # Short delay to ensure command is sent
            read_response(ser)
            
    except KeyboardInterrupt:
        print("Exiting")

    finally:
        ser.close()  # Close the serial connection

if __name__ == '__main__':
    main()
