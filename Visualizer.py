import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datastream import UARTParser
import time

class LiveSensorVisualization:
    def __init__(self):
        # Setup the figure with two subplots
        self.fig = plt.figure(figsize=(15, 6))
        
        # 3D Point Cloud Plot
        self.ax1 = self.fig.add_subplot(121, projection='3d')
        self.ax1.set_title('Point Cloud Data')
        self.ax1.set_xlabel('X')
        self.ax1.set_ylabel('Y')
        self.ax1.set_zlabel('Z')
        
        # Height Data Plot
        self.ax2 = self.fig.add_subplot(122)
        self.ax2.set_title('Height Data')
        self.ax2.set_xlabel('Track ID')
        self.ax2.set_ylabel('Height')
        
        # UART Parser setup
        self.parser = UARTParser(type="DoubleCOMPort")
        
        # Plot settings
        plt.tight_layout()
        plt.ion()  # Turn on interactive mode

    def connect_com_ports(self, cli_com, data_com):
        """Connect to the specified COM ports"""
        self.parser.connectComPorts(cli_com, data_com)

    def update_visualization(self):
        """
        Read UART data and update the visualization
        """
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        
        # Read and parse UART data
        trial_output = self.parser.readAndParseUartDoubleCOMPort()
        
        # Extract point cloud and height data
        point_cloud = trial_output['pointCloud']
        height_data = trial_output['heightData']
        
        # 3D Point Cloud Visualization
        self.ax1.set_title('Point Cloud Data')
        self.ax1.set_xlabel('X')
        self.ax1.set_ylabel('Y')
        self.ax1.set_zlabel('Z')
        self.ax1.scatter(
            point_cloud[:, 0],  # X coordinates
            point_cloud[:, 1],  # Y coordinates
            point_cloud[:, 2],  # Z coordinates
            c=point_cloud[:, 6],  # Color based on the last column
            cmap='viridis'
        )
        
        # Height Data Visualization
        self.ax2.set_title('Height Data')
        self.ax2.set_xlabel('Track ID')
        self.ax2.set_ylabel('Height')
        
        # Plot height data as a bar chart
        track_ids = height_data[:, 0]
        heights = height_data[:, 2]
        
        self.ax2.bar(track_ids, heights)
        
        # Update the plot
        plt.draw()
        plt.pause(0.1)

    def run_visualization(self):
        """
        Continuously update and display visualization
        """
        try:
            plt.show(block=False)
            while True:
                self.update_visualization()
                plt.pause(0.1)
        except KeyboardInterrupt:
            print("Visualization stopped.")
        finally:
            plt.close()

def main():
    # Get COM port inputs
    cliCom = input("Enter the CLI COM port: ")
    dataCom = input("Enter the Data COM port: ")

    # Create and run visualization
    visualizer = LiveSensorVisualization()
    visualizer.connect_com_ports(cliCom, dataCom)
    visualizer.run_visualization()

if __name__ == "__main__":
    main()