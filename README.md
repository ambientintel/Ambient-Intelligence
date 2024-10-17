# Ambient-Intelligence
Modified Industrial Visualizer for People Tracking

Sensor: IWR6843<br/>
Datasheet link: [https://www.ti.com/product/IWR6843#reference-designs](url)

## Application Visualizer source code:
C:\ti\radar_toolbox_2_20_00_05\tools\visualizers\Applications_Visualizer

## Circuit Board Design Info


### Flash Setup:

Location: C:\ti\radar_toolbox_2_20_00_05\source\ti\examples\People_Tracking\3D_People_Tracking\prebuilt_binaries

![image](https://github.com/user-attachments/assets/a187bb92-6799-4768-938e-4e438d84f819)

Enhanced port speed: 115200<br/>
Data port speed: 921600

## Config file for accurate fall Detection in Industrial Visualizer

Download `Final_config_6m.cfg` to location `'C:\ti\radar_toolbox_2_20_00_05\source\ti\examples\People_Tracking\3D_People_Tracking\chirp_configs'`. Below are instructions to configure the file based on individual preferences:

- **staticBoundaryBox**: [Xmin] [Xmax] [Ymin] [yMax] [Zmin] [Zmax]<br/>
This sets boundaries where static points can be used by the tracker and tracks are allowed to become static. Each value denotes an edge of the 3D cube. Currently, it is recommend to keep minY greater than or equal to 2.

- **boundaryBox**: [Xmin] [Xmax] [Ymin] [yMax] [Zmin] [Zmax]<br/>
This sets boundaries where tracks can exists. Only points inside the box will be used by the tracker. Each value denotes an edge of the 3D cube.

### Configuration Parameters for the Group Tracker and their CLI commands

| Parameter sets  | CLI Commands | Description |
| ------------- | ------------- | ------------- |
| Scenery Parameters  | boundaryBox, staticBoundaryBox, sensorPosition, presenceBoundaryBox  | These define the dimensions of the physical space in which the tracker will operate. These also specify the radar sensor orientation and position. Any measurement points outside these boundary boxes will not be used by the tracker.  |
| Gating Parameters  | Content Cell  | Content Cell  |
| Allocation Parameters  | Content Cell  | Content Cell  |
| State Parameters  | Content Cell  | Content Cell  |
| Max Acceleration Parameters  | Content Cell  | Content Cell  |
| Tracker Configuration Parameters  | Content Cell  | Content Cell  |


