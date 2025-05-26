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
  - [Setting Up Autostart (Linux/Raspberry Pi)](#setting-up-autostart-linuxraspberry-pi)
  - [Create Virtual Environment](#create-a-virtual-environment)
  - [Troubleshooting](#troubleshooting)
- [Processed Data](#processed-data)
- [Raspberry Pi Connect (Beta)](#raspberry-pi-connect-beta)
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

The input to the group tracker is a set of measurement points from the detection layer called the "point cloud". Each of the measurement point obtained from the detection layer includes in spherical coordinates the measured range, azimuth, elevation, and radial velocity of the point. The tracker motion model used is a 3D constant acceleration model characterized by a 9 element State vector S: [𝑥(𝑛) 𝑦(𝑛) 𝑧(𝑛) 𝑥̇(𝑛) 𝑦̇(𝑛) 𝑧̇(𝑛) 𝑥̈(𝑛) 𝑦̈(𝑛) 𝑧̈(𝑛)] in Cartesian space. It should be noted that the measurement vector is related to the state vector through a non-linear transformation (due to trigonometric operations required to convert from spherical to Cartesian coordinates). A variant of Kalman Filter called the Extended Kalman Filter (EKF) is used in the group tracker that linearizes the nonlinear function using the derivative of the non-linear function around current state estimates. Please refer to the group tracker implementation guide for more details on the algorithm [1].



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

### Setting Up Autostart (Linux/Raspberry Pi)

To configure the system to automatically start the fall detection application on boot, follow these steps:

#### Step 1: Clone and Setup the Repository
1. Open a terminal and clone the repository:
   ```bash
   git clone https://github.com/Turtlelord-2k/Ambient-Intelligence.git
   ```

2. Navigate to the repository directory:
   ```bash
   cd Ambient-Intelligence
   ```

3. Update to the latest version:
   ```bash
   git pull origin main
   ```

#### Step 2: Configure Autostart with Crontab
1. Open the crontab editor:
   ```bash
   crontab -e
   ```

2. If prompted to choose an editor, select option 1 (nano) and press Enter.

3. Navigate to the bottom of the file and add the following line:
   ```bash
   @reboot python3 /home/YOUR_USERNAME/Ambient-Intelligence/main.py > /home/YOUR_USERNAME/fall-detection-log.txt 2>&1
   ```
   
   > **Important**: Replace `YOUR_USERNAME` with your actual system username. You can find your username by running `whoami` in the terminal.

4. Save and exit the editor:
   - Press `Ctrl + X`
   - Press `Y` to confirm changes
   - Press `Enter` to save

#### Step 3: Configure the Config File Path
1. Open the main.py file in a text editor:
   ```bash
   geany main.py
   ```
   
   > **Note**: If `geany` is not installed, you can use `nano main.py` or any other text editor like `vim` or `code`.

2. Locate the config file in your repository directory and copy its full path:
   - Navigate to your repository folder in the file manager
   - Right-click on `Final_config_6m.cfg`
   - Select "Copy path" or "Copy location"

3. In the text editor, navigate to line 214 and replace:
   ```python
   c.parseCfg("Final_config_6m.cfg")
   ```
   with:
   ```python
   c.parseCfg("/full/path/to/your/Final_config_6m.cfg")
   ```
   
   > **Example**: If your username is `pi` and you cloned to the home directory, the path would be:
   > ```python
   > c.parseCfg("/home/pi/Ambient-Intelligence/Final_config_6m.cfg")
   > ```

4. Save the file (`Ctrl + S`) and close the editor.

#### Step 4: Test the Setup
1. Reboot your system to test the autostart functionality:
   ```bash
   sudo reboot
   ```

2. After reboot, check if the application is running:
   ```bash
   ps aux | grep python
   ```

3. You can also check the log file for any startup messages or errors:
   ```bash
   cat ~/fall-detection-log.txt
   ```

#### Additional Notes:
- The log file (`fall-detection-log.txt`) will contain all output from the application, including any error messages.
- If you need to stop the autostart service, edit the crontab again (`crontab -e`) and comment out or remove the line by adding a `#` at the beginning.
- Make sure your device is properly connected before the system boots up for the autostart to work correctly.

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

## Raspberry Pi Connect (Beta)
### Introduction

Raspberry Pi Connect provides secure access to your Raspberry Pi from anywhere in the world.

![image](https://github.com/user-attachments/assets/e5f07b70-f546-40de-861b-50631f36bfe4)

To use Connect, install the Connect software and link your device with an account on your Raspberry Pi. Then visit connect.raspberrypi.com to access the desktop or a shell running on your Raspberry Pi in a browser window.

Connect uses a secure, encrypted connection. By default, Connect communicates directly between your Raspberry Pi and your browser. However, when Connect can't establish a direct connection between your Raspberry Pi and your browser, we use a relay server. In such cases, Raspberry Pi only retains the metadata required to operate Connect.

Connect is currently in the Beta phase of development.

> [!NOTE]
> To use Connect, your Raspberry Pi must run [Raspberry Pi OS Bookworm](https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/) or later.

### Install

If Connect isn't already installed in your version of Raspberry Pi OS, open a Terminal window. Run the following command to update your system and packages:

```bash
$ sudo apt update
$ sudo apt full-upgrade
```

Run the following command on your Raspberry Pi to install Connect:

```bash
$ sudo apt install rpi-connect
```

You can also install Connect from the Recommended Software application.

After installation, use the `rpi-connect` command line interface to start Connect for your current user:

```bash
$ rpi-connect on
```

Alternatively, click the Connect icon in the menu bar to open a dropdown menu and select Turn On Raspberry Pi Connect:
![image](https://github.com/user-attachments/assets/5ef09ef1-7ffe-4c24-a374-6202825bb128)

### Manually start and stop Connect

To start Connect from the command line, run the following command:
```bash
rpi-connect on
```
To stop Connect, run the following command:
```bash
rpi-connect off
```

### Link a Raspberry Pi device with a Connect account

Now that you've installed and started Connect on your Raspberry Pi device, you must associate your device with your Connect account.

Use the following command to generate a link that will connect your device with your Connect account:
```bash
rpi-connect signing
```
This command should output something like the following:
```bash
Complete sign in by visiting https://connect.raspberrypi.com/verify/XXXX-XXXX
```
Visit the verification URL on any device and sign in with your Raspberry Pi ID to link your device with your Connect account.

### Finish linking your Raspberry Pi

After authenticating, assign a name to your device. Choose a name that uniquely identifies the device. Click the Create device and sign in button to continue.
![image](https://github.com/user-attachments/assets/1684989b-1230-4f68-983b-e21971d16f4e)

You can now remotely connect to your device. The Connect icon in your menu bar will turn blue to indicate that your device is now signed in to the Connect service. You should receive an email notification indicating that a new device is linked to your Connect account.
![image](https://github.com/user-attachments/assets/44d4bab0-8194-4218-a801-040dcab6aeb2)

> [!WARNING]
> If you receive an email that says a device that you do not recognise has signed into Connect, change your Raspberry Pi ID password immediately. Remove the device from Connect to permanently disassociate it from your account. Consider enabling two-factor authentication to keep your account secure.

> [!WARNING]
> Connect signs communication with your device serial number. Moving your SD card between devices will sign you out of Connect.


---

### Contribution

Feel free to fork this repository and submit pull requests for improvements or fixes.

---

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.




