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

    # Reset mmWave radar and internal state
    def reset_radar(self):
        """Reset the mmWave radar and all tracking states before starting the algorithm."""
        print("Resetting mmWave radar...")
        
        # Use the dedicated reset method in the UARTParser class
        if self.parser.reset_radar_device():
            # Reset the tracking state
            self.tracking_data = []
            self.frames = []
            self.uartCounter = 0
            
            # Create a fresh FallDetection instance to reset all internal buffers and state
            self.fallDetection = FallDetection()
            
            # Parse and send the configuration
            self.parseCfg("Final_config_6m.cfg")
            self.sendCfg()
            
            print("Radar reset complete.")
            return True
        else:
            print("Failed to reset radar. Check connections and try again.")
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
    
    # Determine COM ports based on operating system
    system = platform.system()
    cliCom = None
    dataCom = None
    
    if system == "Linux":
        cliCom = '/dev/ttyUSB0'
        dataCom = '/dev/ttyUSB1'
    elif system == "Windows":
        for port in serialPorts:
            if (CLI_SIL_SERIAL_PORT_NAME in port.description):   
                cliCom = port.device
            if (DATA_SIL_SERIAL_PORT_NAME in port.description):
                dataCom = port.device
                
    # Prompt user if ports not automatically detected
    if not cliCom or not dataCom:
        cliCom = input("CLI COM port not found for devices. Please enter the CLI COM port: ")
        dataCom = input("DATA COM port not found for devices. Please enter the DATA COM port: ")

    # Create core instance and connect to radar
    c = core()
    try:
        print(f"Connecting to radar on ports CLI: {cliCom}, DATA: {dataCom}")
        c.parser.connectComPorts(cliCom, dataCom)
        
        # Reset the radar before starting the algorithm
        if not c.reset_radar():
            print("ERROR: Failed to reset the radar. Attempting to continue anyway...")
        
        print("Starting fall detection algorithm...")
        # Main processing loop
        while True:
            try:
                trial_output = c.parser.readAndParseUartDoubleCOMPort()
                
                # Process data
                data = {'cfg': c.cfg, 'demo': c.demo, 'device': c.device}
                c.uartCounter += 1
                frameJSON = {}
                
                # Extract frame number
                if ('frameNum' not in trial_output.keys()):
                    print("ERROR: No frame number data in frame")
                    frameJSON['framenumber'] = 0
                else:
                    frameJSON['frameNumber'] = trial_output['frameNum'] 
                
                # Extract height data
                if ('heightData' not in trial_output.keys()):
                    print("ERROR: No height data in frame")
                    frameJSON['HeightData'] = []
                else:
                    frameJSON['HeightData'] = trial_output['heightData'].tolist()
                    print("Height Data: ", frameJSON['HeightData'])

                # Add timestamp
                frameJSON['timestamp'] = time.time()
                frameJSON['CurrTime'] = time.ctime(frameJSON['timestamp']) # Add human-readable timestamp

                # Extract point detection data
                if ('numDetectedPoints' not in trial_output.keys()):
                    print("ERROR: No points detected in frame")
                    frameJSON['PointsDetected'] = 0
                else:
                    frameJSON['PointsDetected'] = trial_output['numDetectedPoints']

                # Process height data if available
                if ('heightData' in trial_output):
                    if (len(trial_output['heightData']) != len(trial_output['trackData'])):
                        print("WARNING: number of heights does not match number of tracks")

                    # For each height for current tracks
                    for height in trial_output['heightData']:
                        # Find track with correct TID
                        for track in trial_output['trackData']:
                            # Found correct track
                            if (int(track[0]) == int(height[0])):
                                tid = int(height[0])
                                height_str = 'tid : ' + str(height[0]) + ', height : ' + str(round(height[1], 2)) + ' m'
                                
                                # Run fall detection algorithm and check results
                                fallDetectionDisplayResults = c.fallDetection.step(trial_output['heightData'], trial_output['trackData'])
                                if (fallDetectionDisplayResults[tid] > 0): 
                                    height_str = height_str + " FALL DETECTED"
                                    print("Alert: Fall Detected for Patient")
                                    
                # Save data to frames
                c.frames.append(frameJSON)
                data['data'] = c.frames
                
                # Write data to file periodically
                if (c.uartCounter % c.framesPerFile == 0):
                    if(c.first_file is True): 
                        if(os.path.exists('TrackingData/') == False):
                            os.mkdir('TrackingData/')
                        os.mkdir('TrackingData/'+c.filepath)
                        c.first_file = False
                    with open('./TrackingData/'+c.filepath+'/replay_' + str(math.floor(c.uartCounter/c.framesPerFile)) + '.json', 'w') as fp:
                        json_object = json.dumps(data, indent=4)
                        fp.write(json_object)
                        c.frames = [] # Reset frames after writing
                        
            except KeyboardInterrupt:
                print("\nStopping fall detection system...")
                # Stop the sensor before exiting
                if hasattr(c.parser, 'cliCom') and c.parser.cliCom.is_open:
                    c.parser.cliCom.write("sensorStop\n".encode())
                break
                
            except Exception as e:
                print(f"ERROR in main loop: {e}")
                # If there's an error, attempt to reset the radar and continue
                print("Attempting to reset the radar...")
                c.reset_radar()
    
    except Exception as e:
        print(f"Fatal error: {e}")
    
    finally:
        # Close connections
        if hasattr(c.parser, 'cliCom') and c.parser.cliCom.is_open:
            c.parser.cliCom.close()
        if hasattr(c.parser, 'dataCom') and c.parser.dataCom.is_open:
            c.parser.dataCom.close()
        print("Fall detection system stopped. All connections closed.")
    