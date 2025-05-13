# Fall Detection System using mmWave Radar Sensor and Raspberry Pi Zero 2W

## System Overview

The fall detection system uses a Texas Instruments IWR6843 mmWave radar sensor connected to a Raspberry Pi Zero 2W to detect falls in real-time. The system processes radar data to track individuals in 3D space and analyzes their movements to identify potential fall events.

```
                 +----------------+         +-----------------+
                 |                |         |                 |
                 |  mmWave Radar  |-------->| Raspberry Pi    |
                 |  Sensor        |  UART   | Zero 2W         |
                 |  (IWR6843)     |         |                 |
                 |                |         |                 |
                 +----------------+         +-----------------+
                                                    |
                                                    | Data Processing
                                                    v
                                           +-----------------+
                                           |                 |
                                           | Fall Detection  |
                                           | Algorithm       |
                                           |                 |
                                           +-----------------+
                                                    |
                                                    | Fall Alert
                                                    v
                                           +-----------------+
                                           |                 |
                                           | Alert System    |
                                           | (AWS IoT etc.)  |
                                           |                 |
                                           +-----------------+
```

## Hardware Components

1. **mmWave Radar Sensor (IWR6843)**:
   - Transmits and receives radio frequency signals
   - Detects people and their movements in 3D space
   - Connected to the Raspberry Pi via UART

2. **Raspberry Pi Zero 2W**:
   - Processes the data from the mmWave radar sensor
   - Runs the fall detection algorithm
   - Sends alerts when falls are detected
   - Can be accessed remotely using Raspberry Pi Connect

## Software Architecture

The fall detection system follows a layered architecture:

```
+----------------------------------------------------------+
|                     Application Layer                     |
| +--------------------------------------------------------+
| |                      main.py                           |
| +--------------------------------------------------------+
+----------------------------------------------------------+
|                     Processing Layer                      |
| +--------------------------------------------------------+
| | fall_detection.py / new_fall_detection.py              |
| +--------------------------------------------------------+
+----------------------------------------------------------+
|                      Data Layer                           |
| +--------------------------------------------------------+
| | datastream.py  |  parseFrame.py  |  parseTLVs.py       |
| +--------------------------------------------------------+
+----------------------------------------------------------+
|                   Configuration Layer                     |
| +--------------------------------------------------------+
| |           Final_config_6m.cfg / roof_mount_config.cfg  |
| +--------------------------------------------------------+
+----------------------------------------------------------+
```

## Data Flow Diagram

```
+---------------+    +---------------+    +---------------+    +---------------+
|               |    |               |    |               |    |               |
| mmWave Radar  |--->| UART Parser   |--->| TLV Parsing   |--->| Data          |
| Sends Data    |    | Captures Data |    | Process Data  |    | Processing    |
|               |    |               |    |               |    |               |
+---------------+    +---------------+    +---------------+    +---------------+
                                                                      |
                                                                      v
+---------------+    +---------------+    +---------------+    +---------------+
|               |    |               |    |               |    |               |
| Alert         |<---| Fall          |<---| Height Data   |<---| Track Data    |
| Generation    |    | Detection     |    | Analysis      |    | Processing    |
|               |    | Algorithm     |    |               |    |               |
+---------------+    +---------------+    +---------------+    +---------------+
```

## Radar Configuration and Signal Processing Chain

The mmWave radar sensor is configured with specific parameters defined in `Final_config_6m.cfg` file:

```
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| Radar Transmits  |--->| Reflections      |--->| Signal           |
| RF Signals       |    | Received         |    | Processing       |
|                  |    |                  |    |                  |
+------------------+    +------------------+    +------------------+
                                                        |
                                                        v
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| Point Cloud      |--->| Target Tracking  |--->| 3D Position      |
| Generation       |    | Algorithm        |    | & Height Data    |
|                  |    |                  |    |                  |
+------------------+    +------------------+    +------------------+
```

The radar sensor is configured with:
- Field of view: 70 degrees horizontal and vertical
- Range: Up to 8 meters
- Detection boundaries: -4 to 4 meters (X), 0 to 8 meters (Y), 0 to 3 meters (Z)
- Tracking boundaries: -3 to 3 meters (X), 0.5 to 7.5 meters (Y), 0 to 3 meters (Z)

## Fall Detection Algorithm

The system includes two fall detection implementations:
1. Basic fall detection algorithm (`fall_detection.py`)
2. Enhanced fall detection algorithm (`new_fall_detection.py`)

### Basic Fall Detection Algorithm

```
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| Height Data      |--->| Height History   |--->| Height Ratio     |
| Collection       |    | Buffer           |    | Calculation      |
|                  |    |                  |    |                  |
+------------------+    +------------------+    +------------------+
                                                        |
                                                        v
                        +------------------+    +------------------+
                        |                  |    |                  |
                        | Fall Detection   |<---| Threshold        |
                        | Logic           |    | Comparison       |
                        |                  |    |                  |
                        +------------------+    +------------------+
```

The basic algorithm works by:
1. Collecting height data for each tracked person
2. Maintaining a buffer of historical height values
3. Comparing current height to historical height
4. Detecting a fall when the ratio falls below a threshold

### Enhanced Fall Detection Algorithm

```
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| Height, Position |    | Multi-parameter  |    | Height Ratio,    |
| Data Collection  |--->| Buffers          |--->| Velocity,        |
|                  |    |                  |    | Acceleration     |
+------------------+    +------------------+    +------------------+
                                                        |
                                                        v
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| Confidence Score |<---| Multi-criteria   |<---| Parameter        |
| Calculation      |    | Analysis         |    | Thresholds       |
|                  |    |                  |    |                  |
+------------------+    +------------------+    +------------------+
                |
                v
+------------------+    +------------------+
|                  |    |                  |
| Fall Alert       |<---| Confidence       |
| Generation       |    | Threshold Check  |
|                  |    |                  |
+------------------+    +------------------+
```

The enhanced algorithm offers:
1. Multi-parameter analysis (height, velocity, acceleration)
2. Confidence scoring mechanism
3. Fall alert generation with confidence values
4. Cooldown periods to prevent duplicate alerts
5. Position tracking for fall location identification

## Connection and Communication

```
                   +--------------------+
                   |                    |
                   |  Texas Instruments |
                   |  mmWave Radar      |
                   |  Sensor (IWR6843)  |
                   |                    |
                   +--------------------+
                        |         |
                        |         |
            +-----------+         +-----------+
            |                                 |
            v                                 v
+--------------------+           +--------------------+
|                    |           |                    |
| Data COM Port      |           | CLI COM Port       |
| (921600 baud)      |           | (115200 baud)      |
|                    |           |                    |
+--------------------+           +--------------------+
            |                                 |
            |                                 |
            v                                 v
+-------------------------------------------------------+
|                                                       |
|                   Raspberry Pi Zero 2W                |
|                                                       |
+-------------------------------------------------------+
                        |
                        v
+-------------------------------------------------------+
|                                                       |
|          Remote Access via Pi Connect                 |
|                                                       |
+-------------------------------------------------------+
```

The system uses:
1. Two UART connections between the radar and Raspberry Pi:
   - Enhanced COM Port (CLI) at 115200 baud
   - Standard COM Port (Data) at 921600 baud
2. Remote access via Raspberry Pi Connect service

## Data Processing Steps

1. **Radar Initialization**:
   - Radar is configured with parameters from the config file
   - Boundary boxes are set up to define the detection area

2. **Data Acquisition**:
   - UART parser reads data from the radar sensor
   - Data is parsed into frames with Type-Length-Value (TLV) format

3. **Point Cloud Generation**:
   - Raw data is converted to 3D point cloud
   - Points represent detected objects in the environment

4. **Tracking**:
   - Points are grouped into tracks representing people
   - Each track has position, velocity, and acceleration data

5. **Height Extraction**:
   - Height data is extracted for each tracked person
   - Height is the key parameter for fall detection

6. **Fall Detection**:
   - Height data is analyzed over time
   - Sudden changes in height trigger fall detection
   - Enhanced algorithm adds velocity and acceleration analysis

7. **Alert Generation**:
   - When fall is detected, alerts are generated
   - Alerts include track ID, confidence score, and position

## System Implementation on Raspberry Pi Zero 2W

```
+--------------------+     +--------------------+     +--------------------+
|                    |     |                    |     |                    |
| Raspberry Pi OS    |     | Python Environment |     | Fall Detection     |
| Bookworm           |---->| with Dependencies  |---->| Application        |
|                    |     |                    |     |                    |
+--------------------+     +--------------------+     +--------------------+
```

The Raspberry Pi requires:
1. Raspberry Pi OS Bookworm or later
2. Python 3.8 or later
3. Required Python packages (from requirements.txt):
   - serial
   - numpy
   - matplotlib
   - json_fix
   - pyserial
   - AWSIoTPythonSDK

## Data Storage

The system stores processed data for later analysis:
```
+--------------------+     +--------------------+
|                    |     |                    |
| Processed Data     |---->| JSON File Storage  |
| from Each Frame    |     | in TrackingData/   |
|                    |     |                    |
+--------------------+     +--------------------+
```

## Conclusion

The fall detection system uses advanced mmWave radar technology to monitor individuals in real-time without privacy concerns associated with camera-based systems. The radar can penetrate through non-metallic materials, allowing for detection even when individuals are not in direct line of sight.

The fall detection algorithm analyzes height, velocity, and acceleration data to accurately detect falls while minimizing false positives. The system is designed to run on a Raspberry Pi Zero 2W, making it a low-cost, reliable solution for fall detection in home and institutional settings. 