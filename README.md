# Ambient-Intelligence
Modified Industrial Visualizer for People Tracking

Sensor: IWR6843< br / >
Datasheet link: [https://www.ti.com/product/IWR6843#reference-designs](url)

## Application Visualizer source code:
C:\ti\radar_toolbox_2_20_00_05\tools\visualizers\Applications_Visualizer

### Flash Setup:

Location: C:\ti\radar_toolbox_2_20_00_05\source\ti\examples\People_Tracking\3D_People_Tracking\prebuilt_binaries

![image](https://github.com/user-attachments/assets/a187bb92-6799-4768-938e-4e438d84f819)

Enhanced port speed: 115200< br / >
Data port speed: 921600

## Config file for accurate fall Detection in Industrial Visualizer

Download `Final_config_6m.cfg` to location `'C:\ti\radar_toolbox_2_20_00_05\source\ti\examples\People_Tracking\3D_People_Tracking\chirp_configs'`. Below are instructions to configure the file based on individual preferences:
-**staticBoundaryBox**: [Xmin] [Xmax] [Ymin] [yMax] [Zmin] [Zmax]
This sets boundaries where static points can be used by the tracker and tracks are allowed to become static. Each value denotes an edge of the 3D cube. Currently, it is recommend to keep minY greater than or equal to 2.
-**boundaryBox**: [Xmin] [Xmax] [Ymin] [yMax] [Zmin] [Zmax]
This sets boundaries where tracks can exists. Only points inside the box will be used by the tracker. Each value denotes an edge of the 3D cube.


