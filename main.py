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
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
from PySide6.QtCore import QTimer

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
        self.parseTimer = QTimer
        self.frameTime = 25

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
            self.parseTimer.start(int(self.frameTime))  # need this line
        except Exception as e:
            print(e)
            print("Parsing .cfg file failed. Did you select the right file?")

    def gracefulReset(self):
        self.parseTimer.stop()
        # self.uart_thread.stop()
        if self.parser.cliCom is not None:
            self.parser.cliCom.close()
        if self.parser.dataCom is not None:
            self.parser.dataCom.close()
        # for demo in self.demoClassDict.values():
        #     if hasattr(demo, "plot_3d_thread"):
        #         demo.plot_3d_thread.stop()
        #     if hasattr(demo, "plot_3d"):
        #         demo.removeAllBoundBoxes()

class AWSIoTPublisher:
    def __init__(self, endpoint, client_id, cert_path, key_path, root_ca_path):
        self.client = AWSIoTPyMQTT.AWSIoTMQTTClient(client_id)
        self.client.configureEndpoint(endpoint, 8883)
        self.client.configureCredentials(root_ca_path, key_path, cert_path)
        
        # Configure connection parameters
        self.client.configureAutoReconnectBackoffTime(1, 32, 20)
        self.client.configureOfflinePublishQueueing(-1)  # Infinite publishing queue
        self.client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.client.configureMQTTOperationTimeout(5)  # 5 sec
        
        # Connect to AWS IoT
        self.client.connect()
        print("AWS IoT connected")
        
        # Topic to publish messages
        self.topic = "fall_detection/logs"
    
    def publish(self, message):
        """Publish a message to the AWS IoT topic"""
        payload = json.dumps({"message": message, "timestamp": time.time()})
        self.client.publish(self.topic, payload, 0)

# Custom print function that redirects to AWS IoT
class IoTPrinter:
    def __init__(self, aws_publisher):
        self.aws_publisher = aws_publisher
        self.original_print = print
    
    def custom_print(self, *args, **kwargs):
        # Convert args to a string
        message = " ".join(map(str, args))
        
        # Print to console as usual
        self.original_print(*args, **kwargs)
        
        # Send to AWS IoT
        self.aws_publisher.publish(message)

if __name__=="__main__":

    ENDPOINT = "d09740292g72j5i9siw7z-ats.iot.us-east-2.amazonaws.com"
    CLIENT_ID = "fall_detection_device"
    CERT_PATH = "./AWS_IoT/a8f9fb40829e5c654a89bdeffa96037716ca94d299f0c0e8c5428767455110f8-certificate.pem.crt"
    KEY_PATH = "./AWS_IoT/a8f9fb40829e5c654a89bdeffa96037716ca94d299f0c0e8c5428767455110f8-private.pem.key"
    ROOT_CA_PATH = "./AWS_IoT/rootCA.pem"

    try:
        aws_publisher = AWSIoTPublisher(ENDPOINT, CLIENT_ID, CERT_PATH, KEY_PATH, ROOT_CA_PATH)
        
        # Setup custom print function
        iot_printer = IoTPrinter(aws_publisher)
        
        # Replace the built-in print function with our custom one
        builtins_print = print
        print = iot_printer.custom_print
        
        print("AWS IoT connection established successfully")
    except Exception as e:
        print(f"Error setting up AWS IoT: {str(e)}")
        print("Continuing with local printing only")


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
    # c.gracefulReset()
    c.parser.connectComPorts(cliCom, dataCom)
    c.parseCfg("Final_config_6m.cfg")
    c.sendCfg()



    while True:
        trial_output = c.parser.readAndParseUartDoubleCOMPort()
        # print("Read and parse UART")
        # print(trial_output)

        try:    
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

            # print(c.fallDetection.heightBuffer)
        
        except KeyboardInterrupt:
            print("Keyboard Interrupt Detected. Stopping program.")
            c.gracefulReset()
            break
    