from datastream import UARTParser
import json
import datetime
import threading
import os
import time
import math
import numpy as np
from fall_detection import FallDetection 
from serial.tools import list_ports
from contextlib import suppress
import sys
import platform
import serial  # Added for reset functionality

class core:
    def __init__(self):
        self.parser = UARTParser(type="DoubleCOMPort")
        self.tracking_data = []
        self.save_lock = threading.Lock()
        self.frames = []
        self.framesPerFile = 100
        self.filepath = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        self.cfg = ""
        self.demo = "3D People Tracking"
        self.device = "xWR6843"
        self.uartCounter = 0
        self.first_file = True
        self.fallDetection = FallDetection()
        self.cli_port = None  # Will store the CLI port name
        self.data_port = None  # Will store the DATA port name

    def power_cycle_device(self):
        """Reset the TI6843AOP device by sending reset command over UART"""
        try:
            if not self.cli_port:
                print("Error: CLI port not defined")
                return False
                
            # Open CLI port for sending reset command
            ser = serial.Serial(self.cli_port, 115200, timeout=1)
            
            # Reset command - replace with actual command if different
            reset_command = b'\x02\x00\x05\x00\x00\x05\x04'
            
            print(f"Sending reset command to device on {self.cli_port}...")
            # Send reset command
            ser.write(reset_command)
            
            # Wait for device to reset
            time.sleep(2)
            
            # Close the connection
            ser.close()
            print("Device reset command sent successfully")
            return True
        except serial.SerialException as e:
            print(f"Error resetting device: {e}")
            return False

    def parseCfg(self, fname):
        # if (self.replay):
        #     self.cfg = self.data['cfg']
        # else:
        with open(fname, "r") as cfg_file:
            self.cfg = cfg_file.readlines()
            self.parser.cfg = self.cfg
            self.parser.demo = self.demo
            self.parser.device = self.device
        for line in self.cfg:
            args = line.split()
            if len(args) > 0:
                # trackingCfg
                if args[0] == "trackingCfg":
                    if len(args) < 5:
                        print("trackingCfg had fewer arguments than expected")
                # Rest of your existing parseCfg method...

    def sendCfg(self):
        try:
            self.parser.sendCfg(self.cfg)
            sys.stdout.flush()
            # self.parseTimer.start(int(self.frameTime))  # need this line
        except Exception as e:
            print(e)
            print("Parsing .cfg file failed. Did you select the right file?")


if __name__=="__main__":
    # Optional: Specify a custom save filepath
    SAVE_FILEPATH = "./Data_files"  # Change this to your desired path
    CLI_SIL_SERIAL_PORT_NAME = 'Enhanced COM Port'
    DATA_SIL_SERIAL_PORT_NAME = 'Standard COM Port'

    serialPorts = list(list_ports.comports())

    
    print("Welcome to the Fall Detection System.")
    # operatingSystem = input("Enter your operating system: ")
    system = platform.system()
    if system  == "Linux":
        cliCom = '/dev/ttyUSB0'
        dataCom = '/dev/ttyUSB1'
    elif system == "Windows":
        for port in serialPorts:
            if (CLI_SIL_SERIAL_PORT_NAME in port.description):   
                cliCom = port.device
            if (DATA_SIL_SERIAL_PORT_NAME in port.description):
                dataCom = port.device
        if (cliCom == None or dataCom == None):    
            cliCom = input("CLI COM port not found for devices. Please enter the CLI COM port: ")
            dataCom = input("DATA COM port not found for devices. Please enter the DATA COM port: ")

    c = core()
    c.cli_port = cliCom  # Store the CLI port in the core object for reset function
    c.data_port = dataCom  # Store the DATA port in the core object
    
    # Add option to reset device at startup
    reset_choice = input("Do you want to reset the device before starting? (y/n): ")
    if reset_choice.lower() == 'y':
        reset_success = c.power_cycle_device()
        if reset_success:
            print("Device reset complete. Continuing with initialization...")
            time.sleep(1)  # Give device time to stabilize after reset
        else:
            print("Device reset failed. Trying to continue anyway...")
    
    # Connect to COM ports
    c.parser.connectComPorts(cliCom, dataCom)
    c.parseCfg("Final_config_6m.cfg")
    c.sendCfg()

    # Add a keyboard interrupt handler to allow manual reset during operation
    try:
        while True:
            trial_output = c.parser.readAndParseUartDoubleCOMPort()
            # print("Read and parse UART")
            # print(trial_output)
            
            data = {'cfg': c.cfg, 'demo': c.demo, 'device': c.device}
            c.uartCounter += 1
            frameJSON = {}
            if ('frameNum' not in trial_output.keys()):
                print("ERROR: No frame number data in frame")
                frameJSON['framenumber'] = 0
            else:
                frameJSON['frameNumber'] = trial_output['frameNum'] 
            
            if ('heightData' not in trial_output.keys()):
                print("ERROR: No height data in frame")
                frameJSON['HeightData'] = []
            else:
                frameJSON['HeightData'] = trial_output['heightData'].tolist()

            frameJSON['timestamp'] = time.time()
            frameJSON['CurrTime'] = time.ctime(frameJSON['timestamp']) # Add human-readable timestamp

            
            if ('numDetectedPoints' not in trial_output.keys()):
                print("ERROR: No points detected in frame")
                frameJSON['PointsDetected'] = 0
            else:
                frameJSON['PointsDetected'] = trial_output['numDetectedPoints']

            if ('heightData' in trial_output):
                if (len(trial_output['heightData']) != len(trial_output['trackData'])):
                    print("WARNING: number of heights does not match number of tracks")

                # For each height heights for current tracks
                for height in trial_output['heightData']:
                    # Find track with correct TID
                    for track in trial_output['trackData']:
                        # Found correct track
                        if (int(track[0]) == int(height[0])):
                            tid = int(height[0])
                            height_str = 'tid : ' + str(height[0]) + ', height : ' + str(round(height[1], 2)) + ' m'
                            # If this track was computed to have fallen, display it on the screen
                            
                            fallDetectionDisplayResults = c.fallDetection.step(trial_output['heightData'], trial_output['trackData'])
                            if (fallDetectionDisplayResults[tid] > 0): 
                                height_str = height_str + " FALL DETECTED"
                                print("Alert: Fall Detected for Patient")
            # frameJSON['fallDetected'] = height_str                                
            c.frames.append(frameJSON)
            data['data'] = c.frames
            # print(data)
            if (c.uartCounter % c.framesPerFile == 0):
                if(c.first_file is True): 
                    if(os.path.exists('TrackingData/') == False):
                        # Note that this will create the folder in the caller's path, not necessarily in the viz folder            
                        os.mkdir('TrackingData/')
                    os.mkdir('TrackingData/'+c.filepath)
                    c.first_file = False
                with open('./TrackingData/'+c.filepath+'/replay_' + str(math.floor(c.uartCounter/c.framesPerFile)) + '.json', 'w') as fp:
                    json_object = json.dumps(data, indent=4)
                    fp.write(json_object)
                    c.frames = [] #uncomment to put data into one file at a time in 100 frame chunks

            # Check for user command to reset device
            if c.uartCounter % 50 == 0:  # Only check periodically to avoid excessive polling
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = input()
                    if line.lower() == 'reset':
                        print("Manual reset requested...")
                        c.power_cycle_device()
                        # Reconnect after reset
                        time.sleep(1)  # Give device time to stabilize
                        c.parser.connectComPorts(cliCom, dataCom)
                        c.sendCfg()
                        print("Reset and reconfiguration complete")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
        # Add option to reset device before exit
        reset_choice = input("Do you want to reset the device before exiting? (y/n): ")
        if reset_choice.lower() == 'y':
            c.power_cycle_device()
        print("Exiting program.")
        sys.exit(0)