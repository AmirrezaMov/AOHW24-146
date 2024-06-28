import struct
import time
import os
import subprocess
from subprocess import Popen
import serial
from hybrid_config_gen import hybrid_config_gen
from config_gen import config_gen
from show import show_h, show_a


VERSAL_TA = 1

print("Connecting and Initializing The Device...")
# subprocess.run(["python3", "hybrid_config_gen.py"], stdout = subprocess.DEVNULL)
xsct = Popen(["xsct"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
line = "source init.tcl\n"
xsct.stdin.write(line.encode('utf-8'))
xsct.stdin.flush()
xsct.stdout.readline()
time.sleep(2)

systems = ['aie-only', 'hybrid']
system = 'hybrid'

models = ['tvb76', 'tvb192', 'tvb998']
model = 'tvb76'

N = 76
M = 2
tf = 3000
dt = 0.05
CMO = 0



while(True):
    command = input('>> ')
    command = command.split()

    try:
        if command[0] == 'run':
            if (command[1] in systems) and (command[2] in models):
                tcl = open("program.tcl", 'w')

                if command[1] == 'aie-only':
                    system = 'aie-only'
                    config_gen(command[2], float(command[3]))
                    tcl.write("mwr -force -bin -file ./Data/config.bin 0x10000000 0x10000000\n")
                elif command[1] == 'hybrid':
                    system = 'hybrid'
                    hybrid_config_gen(command[2], float(command[3]))
                    tcl.write("mwr -force -bin -file ./Data/config_hybrid.bin 0x10000000 0x10000000\n")

                tcl.write("rst -por\n")
                tcl.write("rst -system\n")
                if command[1] == 'aie-only':
                    tcl.write("device program ./Images/AIE-Only.BIN\n")
                elif command[1] == 'hybrid':
                    tcl.write("device program ./Images/Hybrid.BIN\n")

                tcl.close()
                line = "source program.tcl\n"
                xsct.stdin.write(line.encode('utf-8'))
                xsct.stdin.flush()

                N = int(command[2][3:])

            else:
                print("Invalid Arguments")
        
        elif command[0] == 'read':
            path = "Output/output_"
            print('Reading the output from the device...')
            f = open('output_address.txt', 'r')
            address = f.readline()[:-1]
            size = f.readline()[:-1]
            f.close()
            
            tcl = open('read.tcl', 'w')
            cmd = "mrd -force -bin -file ./Output/output_"
            if system == 'aie-only':
                path = path + 'a.bin'
                cmd = cmd + 'a.bin ' + address + ' ' + size + '\n'
            else:
                path = path + 'h.bin'
                cmd = cmd + 'h.bin ' + address + ' ' + size + '\n'
            tcl.write(cmd)
            tcl.close()

            try:
                os.remove(path)
            except:
                pass

            line = "source read.tcl\n"
            xsct.stdin.write(line.encode('utf-8'))
            xsct.stdin.flush()

            while(os.path.isfile(path) == False):
                pass

            print("Done")  

        elif command[0] == 'show':
            if command[1] == 'hybrid':
                if command[2] == 'all':
                    show_h(N, M, tf, CMO, dt)
                else:
                    show_h(N, M, tf, CMO, dt, int(command[2]))
            if command[1] == 'aie-only':
                if command[2] == 'all':
                    show_a(N, M, tf, CMO, dt)
                else:
                    show_a(N, M, tf, CMO, dt, int(command[2]))

        else:
            print("Unknown Command")

    except:
        print("Invalid Command.")



