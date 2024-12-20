from datastream import UARTParser
import json
import datetime
import threading
import os
import time
import math
import numpy as np
from fall_detection import FallDetection 

class core:
    def __init__(self):
        self.parser = UARTParser(type="DoubleCOMPort")
        self.tracking_data = []
        self.save_lock = threading.Lock()
        self.frames = []
        self.framesPerFile = 100
        self.filepath = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        self.cfg = ""
        self.demo = ""
        self.device = "xWR6843"
        self.uartCounter = 0
        self.first_file = True
        self.fallDetection = FallDetection()

# def save_tracking_data(data, filepath=None):
#     """
#     Save tracking data to a JSON file with current timestamp in the filename.
    
#     Args:
#         data (dict): The data to be saved in JSON format
#         filepath (str, optional): Custom filepath for saving. If None, uses default.
#     """
#     # Get current timestamp and format it for the filename
#     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
#     # Determine the filepath
#     if filepath is None:
#         filename = f"TrackingData_{timestamp}.json"
#     else:
#         # Ensure directory exists
#         os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
#         # If filepath is a directory, create filename in that directory
#         if os.path.isdir(filepath):
#             filename = os.path.join(filepath, f"TrackingData_{timestamp}.json")
#         else:
#             filename = filepath
    
#     # Save the data to the JSON file
#     try:
#         with open(filename, 'w') as json_file:
#             json.dump(data, json_file, indent=4)
#         print(f"Data successfully saved to {filename}")
#     except IOError as e:
#         print(f"Error saving file: {e}")

# def periodic_save(core_instance, filepath=None, interval=100):
#     """
#     Periodically save tracking data
    
#     Args:
#         core_instance (core): The core instance containing tracking data
#         filepath (str, optional): Custom filepath for saving
#         interval (int): Interval between saves in seconds
#     """
#     def save_routine():
#         while True:
#             time.sleep(interval)
#             with core_instance.save_lock:
#                 if core_instance.tracking_data:
#                     save_tracking_data(core_instance.tracking_data, filepath)
    
#     # Start the saving thread as a daemon
#     save_thread = threading.Thread(target=save_routine, daemon=True)
#     save_thread.start()
#     return save_thread

if __name__=="__main__":
    # Optional: Specify a custom save filepath
    SAVE_FILEPATH = "./Data_files"  # Change this to your desired path
    
    # cliCom = input("Enter the CLI COM port: ")
    # dataCom = input("Enter the Data COM port: ")

    #for windows
    # cliCom = 'COM5'
    # dataCom = 'COM3'

    #for linux
    cliCom = '/dev/ttyUSB0'
    dataCom = '/dev/ttyUSB1'

    c = core()
    c.parser.connectComPorts(cliCom, dataCom)


    # Start periodic saving thread

    while True:
        trial_output = c.parser.readAndParseUartDoubleCOMPort()
        # print("Read and parse UART")
        # print(trial_output)

            # Add to tracking data list
            # with c.save_lock:
            #     c.tracking_data.append(trial_output)

    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         break
    # periodic_save_thread = periodic_save(c, filepath=SAVE_FILEPATH)
        # fd_buffer = c.fallDetection.step(heights = trial_output['heightData'], tracks = trial_output['trackData'])
        # print(fd_buffer)

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
        frameJSON['fallDetected'] = height_str                                
        c.frames.append(frameJSON)
        data['data'] = c.frames
        # print(data)
        if (c.uartCounter % c.framesPerFile == 0):
            if(c.first_file is True): 
                if(os.path.exists('binData/') == False):
                    # Note that this will create the folder in the caller's path, not necessarily in the viz folder            
                    os.mkdir('binData/')
                os.mkdir('binData/'+c.filepath)
                c.first_file = False
            with open('./binData/'+c.filepath+'/replay_' + str(math.floor(c.uartCounter/c.framesPerFile)) + '.json', 'w') as fp:
                json_object = json.dumps(data, indent=4)
                fp.write(json_object)
                c.frames = [] #uncomment to put data into one file at a time in 100 frame chunks

        # print(c.fallDetection.heightBuffer)