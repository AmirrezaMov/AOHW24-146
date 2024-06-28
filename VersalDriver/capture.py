import os
import serial

   

SERIAL_PORT = "/dev/ttyUSB1"
SERIAL_BAUDRATE = 115200

ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE)

print_words = ['Starting', 'Config', 'Reading', '|', 'Initializing', 'Output', 'Done', 'System', 'Writing', 'AIE', 'Running']

while(True):
    line = ser.readline()
    line = line.decode("utf-8")
    ls = line.split()
    if 'Versal' in ls:
        os.system('clear')
        print("Booting the Device...")
        print("==============================")
    else:
        try:
            if (ls[0] in print_words):
                if ls[0] == '(n':
                    print(line[:-1])
                else:    
                    print(line)
            elif(ls[0] == 'Address'):
                f = open("output_address.txt", 'w')
                f.write(ls[1] + '\n')
                f.write(ls[2] + '\n')
                f.close()
            elif(ls[0] == 'INIT.BIN'):
                print("Initializing the Board...")
                print("Done!")
        except:
            pass

ser.close()


