# Ambient-Intelligence
Modified Industrial Visualizer for People Tracking

Sensor: IWR6843<br/>
Datasheet link: [https://www.ti.com/product/IWR6843#reference-designs](url)

---

## Table of Contents
- [Application Visualizer Source Code](#application-visualizer-source-code)
- [Circuit Board Design Info](#circuit-board-design-info)
- [Flash Setup](#flash-setup)
- [Configuration Files](#config-file-for-accurate-fall-detection-in-industrial-visualizer)
- [Device Architecture and Processing Chain](#device-architecture-and-processing-chain)
- [How to Run the Package](#how-to-run-the-package)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Install Dependencies](#install-dependencies)
  - [Run the Main File](#run-the-main-file)
  - [Troubleshooting](#troubleshooting)
- [Processed Data](#processed-data)
- [Contribution](#contribution)
- [License](#license)

---

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
This sets boundaries where static points can be used by the tracker and tracks are allowed to become static. Each value denotes an edge of the 3D cube. Currently, it is recommend to keep minY greater than or equal to 2.<br/>

| Parameters  | Example Value  | Dimension  | Description  |
| ------------- | ------------- | ------------- | ------------- |
| X-min (float)  | -3  | m  | Minimum horizontal distance with respect to the origin in the World co-ordinates  |
| X-max (float)  | 3  | m  | Maximum horizontal distance with respect to the origin in the World co-ordinates  |
| Y-min (float)  | 0.5  | m  | Minimum vertical distance with respect to the origin in the World co-ordinates  |
| Y-max (float)  | 7.5  | m  | Maximum vertical distance with respect to the origin in the World co-ordinates  |
| Z-min (float)  | 0  | m  | Minimum height with respect to the origin in the World coordinates. Note that Z = 0 corresponds to the ground plane. In some scenarios, we see some valid reflections from below the ground (due to slight errors in sensor mounting parameters) hence we have a negative value.  |
| Z-max (float)  | 3  | m  | Maximum height with respect to the origin in the World coordinates  |

- **boundaryBox**: [Xmin] [Xmax] [Ymin] [yMax] [Zmin] [Zmax]<br/>
This sets boundaries where tracks can exists. Only points inside the box will be used by the tracker. Each value denotes an edge of the 3D cube.

| Parameters  | Example Value | Dimension | Description |
| ------------- | ------------- | ------------- | ------------- |
| X-min (float) | -3.5 | m | Minimum horizontal distance with respect to the origin in the World co-ordinates |
| X-max (float) | 3.5 | m | Maximum horizontal distance with respect to the origin in the World co-ordinates |
| Y-min (float) | 0 | m | Minimum vertical distance with respect to the origin in the World co-ordinates |
| Y-max (float) | 9 | m | Maximum vertical distance with respect to the origin in the World co-ordinates |
| Z-min (float) | -0.5 | m | Minimum height with respect to the origin in the World coordinates. Note that Z = 0 corresponds to the ground plane. In some scenarios, we see some valid reflections from below the ground (due to slight errors in sensor mounting parameters) hence we have a negative value. |
| Z-max (float) | 3 | m | Maximum height with respect to the origin in the World coordinates |



### Configuration Parameters for the Group Tracker and their CLI commands

A high-level description of the parameter sets and the corresponding CLI command

| Parameter sets  | CLI Commands | Description |
| ------------- | ------------- | ------------- |
| Scenery Parameters  | boundaryBox, staticBoundaryBox, sensorPosition, presenceBoundaryBox  | These define the dimensions of the physical space in which the tracker will operate. These also specify the radar sensor orientation and position. Any measurement points outside these boundary boxes will not be used by the tracker.  |
| Gating Parameters  | gatingParam   | These determine the maximum volume and velocity of a tracked object and are used to associate measurement points with tracks that already exist. Points detected beyond the limits set by these parameters will not be included in the set of points that make up the tracked object.  |
| Allocation Parameters  | allocationParam   | These are used to detect new tracks/people in the scene. When detected points are not associated with existing tracks, allocation parameters are used to cluster these remaining points and determine if that cluster qualifies as a person/target.  |
| State Parameters  | stateParam   | The state transition parameters determine the state of a tracking instance. Any tracking instance can be in one of three states: FREE, DETECT, or ACTIVE.  |
| Max Acceleration Parameters  | maxAcceleration   | These parameters determine the maximum acceleration in the lateral, longitudinal, and vertical directions.  |
| Tracker Configuration Parameters  | trackingCfg  | These parameters are used to enable the Tracker Module and determine the amount of memory to allocate based on maximum number of points and tracks. It also configures the radial velocity parameters (initial velocity, velocity resolution, max velocity) and frame rate at which the tracker is to operate.  |

![image](https://github.com/user-attachments/assets/d2c313e1-d05c-42ba-986c-8b66ce53edc3)

For further tuning, refer [here](Documentation/Motion_Presence_Detection_Demo_Group_Tracker_Tuning_Guide.pdf)

## Device architecture and Processing chain

### Tracking module in the overall processing chain
![image](https://github.com/user-attachments/assets/e68dd8bd-bd5d-47b4-9753-bab573356c56)

The input to the group tracker is a set of measurement points from the detection layer called the “point cloud”. Each of the measurement point obtained from the detection layer includes in spherical coordinates the measured range, azimuth, elevation, and radial velocity of the point. The tracker motion model used is a 3D constant acceleration model characterized by a 9 element State vector S: [𝑥(𝑛) 𝑦(𝑛) 𝑧(𝑛) 𝑥̇(𝑛) 𝑦̇(𝑛) 𝑧̇(𝑛) 𝑥̈(𝑛) 𝑦̈(𝑛) 𝑧̈(𝑛)] in Cartesian space. It should be noted that the measurement vector is related to the state vector through a non-linear transformation (due to trigonometric operations required to convert from spherical to Cartesian coordinates). A variant of Kalman Filter called the Extended Kalman Filter (EKF) is used in the group tracker that linearizes the nonlinear function using the derivative of the non-linear function around current state estimates. Please refer to the group tracker implementation guide for more details on the algorithm [1].



## How to run the package
### Prerequisites

Before running the code, ensure you have the following installed on your system:

#### Install Python
Ensure Python (version 3.8 or later) is installed on your system. Open the command prompt on Windows or Terminal in Linux and run the below command to check the current Python version
```bash
python --version
```

If no Python version exists, follow the below instructions

##### On Linux:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

##### On Windows:
1. Download Python from the [official Python website](https://www.python.org/downloads/).
2. During installation, select "Add Python to PATH".
3. Verify the installation:
   ```bash
   python --version
   ```

#### Install Git

##### On Linux:
```bash
sudo apt update
sudo apt install git-all
```

##### On Windows:
1. Download Git for Windows from the [official Git website](https://git-scm.com/).
2. Run the installer and follow the setup instructions.
3. Ensure the option "Add Git to PATH" is selected during installation.
4. Alternatively, you can install Git via pip:
   ```bash
   pip install python-git
   ```
   Note: This method installs the GitPython library for managing Git repositories programmatically. To use Git commands, the standard Git installation is recommended.

To verify the installation, open a terminal or command prompt and run:
```bash
git --version
```
You should see the installed Git version.

---

### Clone the Repository

Use Git to clone this repository to your local machine at your desired directory.

##### On Linux:
```bash
git clone https://github.com/Turtlelord-2k/Ambient-Intelligence.git
cd Ambient-Intelligence
```

##### On Windows:
1. Open Command Prompt or Git Bash.
2. Run the following commands:
   ```bash
   git clone https://github.com/Turtlelord-2k/Ambient-Intelligence.git
   cd Ambient-Intelligence
   ```

### Update the latest Repository onto the local branch

First, navigate to the location where your repository is stored and run the following command to update your local repository with the latest package version. 
```bash
cd Ambient-Intelligence
git pull origin main
```
---

### Create a Virtual Environment

It's recommended to create a virtual environment to isolate the package dependencies from your global Python installation. Navigate to the directory where you have cloned the package and run the below commands.

#### On Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Once activated, your command prompt should show the name of the virtual environment, indicating it's active.

### Install Dependencies

Install the required Python dependencies using `pip`:
```bash
pip install -r requirements.txt
```

---

### Run the Main File

Before running the main file, run the Industrial Visualizer once, then run the main script to execute the project. This tens to run the package smoothly. (This bug is being worked on)

##### On Linux:
```bash
python3 main.py
```

##### On Windows:
```bash
python main.py
```

---

### Troubleshooting

- **Issue**: "Command not found" for `git` or `python`.
  - **Solution**: Ensure Git and Python are correctly installed and added to your system PATH.
- **Issue**: Missing Python dependencies.
  - **Solution**: Check `requirements.txt` and ensure all dependencies are installed using `pip install -r requirements.txt`.

---

Processed Data

The processed sensor data, including height data, will be saved in the binData directory as JSON files.

---

### Contribution

Feel free to fork this repository and submit pull requests for improvements or fixes.

---

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.




