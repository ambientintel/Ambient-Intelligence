from datastream import UARTParser
import json
import datetime
import threading
import os
import time
import math
import numpy as np
from serial.tools import list_ports
from contextlib import suppress
import sys
import platform
# from fall_detection import FallDetection 
from new_fall_detection import FallDetection

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

        # self.demoClassDict = {
        #     DEMO_OOB_x843: OOBx843(),
        #     DEMO_OOB_x432: OOBx432(),
        #     DEMO_3D_PEOPLE_TRACKING: PeopleTracking(),
        #     DEMO_VITALS: VitalSigns(),
        #     DEMO_SMALL_OBSTACLE: SmallObstacle(),
        #     DEMO_GESTURE: GestureRecognition(),
        #     DEMO_SURFACE: SurfaceClassification(),
        #     DEMO_LEVEL_SENSING: LevelSensing(),
        #     DEMO_GROUND_SPEED: TrueGroundSpeed(),
        #     DEMO_LONG_RANGE: LongRangePD(),
        #     DEMO_MOBILE_TRACKER: MobileTracker(),
        #     DEMO_KTO: KickToOpen(),
        #     DEMO_CALIBRATION: Calibration(),
        #     DEMO_DASHCAM: Dashcam(),
        #     DEMO_EBIKES: EBikes(),
        #     DEMO_VIDEO_DOORBELL: VideoDoorbell(),
        #     DEMO_TWO_PASS_VIDEO_DOORBELL: TwoPassVideoDoorbell(),
        # }

    # Populated with all devices and the demos each of them can run
    # DEVICE_DEMO_DICT = {
    #     "xWR6843": {
    #         "isxWRx843": True,
    #         "isxWRLx432": False,
    #         "singleCOM": False,
    #         "demos": [PeopleTracking()]
    #     }
    # }

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
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseTrackingCfg(args)
                elif args[0] == "SceneryParam" or args[0] == "boundaryBox":
                    if len(args) < 7:
                        print(
                            "SceneryParam/boundaryBox had fewer arguments than expected"
                        )
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "frameCfg":
                    if len(args) < 4:
                        print("frameCfg had fewer arguments than expected")
                    # else:
                    #     self.frameTime = float(args[5]) / 2
                # elif args[0] == "sensorPosition":
                    # sensorPosition for x843 family has 3 args
                    # if DEVICE_DEMO_DICT[self.device]["isxWRx843"] and len(args) < 4:
                    #     print("sensorPosition had fewer arguments than expected")
                    # elif DEVICE_DEMO_DICT[self.device]["isxWRLx432"] and len(args) < 6:
                    #     print("sensorPosition had fewer arguments than expected")
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseSensorPosition(
                    #             args, DEVICE_DEMO_DICT[self.device]["isxWRx843"]
                    #         )
                # Only used for Small Obstacle Detection
                # elif args[0] == "occStateMach":
                #     numZones = int(args[1])
                # Only used for Small Obstacle Detection
                elif args[0] == "zoneDef":
                    if len(args) < 8:
                        print("zoneDef had fewer arguments than expected")
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "mpdBoundaryBox":
                    if len(args) < 8:
                        print("mpdBoundaryBox had fewer arguments than expected")
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "chirpComnCfg":
                    if len(args) < 8:
                        print("chirpComnCfg had fewer arguments than expected")
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseChirpComnCfg(args)
                elif args[0] == "chirpTimingCfg":
                    if len(args) < 6:
                        print("chirpTimingCfg had fewer arguments than expected")
                    # else:
                    #     with suppress(AttributeError):
                    #         self.demoClassDict[self.demo].parseChirpTimingCfg(args)
                # TODO This is specifically guiMonitor for 60Lo, this parsing will break the gui when an SDK 3 config is sent
                # elif args[0] == "guiMonitor":
                #     if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
                #         if len(args) < 12:
                #             print("guiMonitor had fewer arguments than expected")
                #         else:
                #             with suppress(AttributeError):
                #                 self.demoClassDict[self.demo].parseGuiMonitor(args)
                # elif args[0] == "presenceDetectCfg":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parsePresenceDetectCfg(args)
                # elif args[0] == "sigProcChainCfg2":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parseSigProcChainCfg2(args)
                elif args[0] == "mpdBoundaryArc":
                    if len(args) < 8:
                        print("mpdBoundaryArc had fewer arguments than expected")
                #     else:
                #         with suppress(AttributeError):
                #             self.demoClassDict[self.demo].parseBoundaryBox(args)
                # elif args[0] == "measureRangeBiasAndRxChanPhase":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parseRangePhaseCfg(args)
                # elif args[0] == "clutterRemoval":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parseClutterRemovalCfg(args)
                # elif args[0] == "sigProcChainCfg":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parseSigProcChainCfg(args)
                # elif args[0] == "channelCfg":
                #     with suppress(AttributeError):
                #         self.demoClassDict[self.demo].parseChannelCfg(args)

        # Initialize 1D plot values based on cfg file
        # with suppress(AttributeError):
        #     self.demoClassDict[self.demo].setRangeValues()

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



    #for linux
    # cliCom = '/dev/ttyUSB0'
    # dataCom = '/dev/ttyUSB1'

    c = core()
    c.parser.connectComPorts(cliCom, dataCom)
    LastByte = c.parser.dataCom.read(1)
    if (len(LastByte) < 1):
        print("Device is not configured, configuring device with default config")
        c.parseCfg("Final_config_6m.cfg")
        c.sendCfg()
    else:
        print("Device is already configured")



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
            print("Height Data: ", frameJSON['HeightData'])

        frameJSON['timestamp'] = time.time()
        frameJSON['CurrTime'] = time.ctime(frameJSON['timestamp']) # Add human-readable timestamp

        
        if ('numDetectedPoints' not in trial_output.keys()):
            print("ERROR: No points detected in frame")
            frameJSON['PointsDetected'] = 0
        else:
            frameJSON['PointsDetected'] = trial_output['numDetectedPoints']

        # Extract track positions if available to pass to new fall detection algorithm
        positions = None
        if 'trackData' in trial_output:
            positions = []
            for track in trial_output['trackData']:
                if len(track) >= 4:  # Make sure there are x, y, z coordinates
                    positions.append((track[1], track[2], track[3]))  # x, y, z

        # Update with the new fall detection implementation
        if ('heightData' in trial_output and 'trackData' in trial_output):
            if (len(trial_output['heightData']) != len(trial_output['trackData'])):
                print("WARNING: number of heights does not match number of tracks")
            
            # Using the enhanced fall detection algorithm with position data
            fallDetectionResults = c.fallDetection.step(trial_output['heightData'], trial_output['trackData'], positions)
            
            # Check for any detected falls
            for tid, fall_status in enumerate(fallDetectionResults):
                if fall_status > 0:
                    print(f"Main Loop - Fall Alert: Track ID {tid} with status {fall_status}")
                    # No need to send alert here as it's already done in the FallDetection class
            
            # Store fall alerts in the frame data
            frameJSON['fallAlerts'] = c.fallDetection.getFallAlerts()
            
            # Print current heights for debug purposes
            # print(f"Current heights: {trial_output['heightData']}")
            for i, height in enumerate(trial_output['heightData']):
                print(f"Track {height[0]}: Height = {height[1]:.2f}m")
            
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