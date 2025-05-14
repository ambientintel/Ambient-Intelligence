from collections import deque
import copy 
import time
import numpy as np

class FallDetection:

    # Initialize the class with the default parameters (tested empirically)
    def __init__(self, maxNumTracks = 30, frameTime = 55, fallingThresholdProportion = 0.6, secondsInFallBuffer = 1.5):
        self.fallingThresholdProportion = fallingThresholdProportion
        self.secondsInFallBuffer = secondsInFallBuffer
        self.heightHistoryLen = int(round(self.secondsInFallBuffer * frameTime))
        self.heightBuffer = [deque([-5] *  self.heightHistoryLen, maxlen =  self.heightHistoryLen) for i in range(maxNumTracks)]
        self.speedBuffer = [deque([0] * self.heightHistoryLen, maxlen = self.heightHistoryLen) for i in range(maxNumTracks)]
        self.tracksIDsInPreviousFrame = []
        self.fallBufferDisplay = [0 for i in range(maxNumTracks)] # Fall results that will be displayed to screen
        self.numFramesToDisplayFall = 100 # How many frames do you want to display a fall on the screen for
        self.lastFallTime = [0 for i in range(maxNumTracks)] # Track the last time a fall was detected for each track
        self.fallCooldownPeriod = 10.0  # Seconds to wait before detecting another fall for the same track
        self.consistentFallFrames = [0 for i in range(maxNumTracks)] # Count of consecutive frames where fall criteria are met
        self.requiredConsistentFrames = 3 # Number of consistent frames required to confirm a fall
        self.minHeightThreshold = 0.3  # Minimum height in meters to consider for fall detection
        self.maxFallSpeed = -0.6  # Maximum negative speed (m/s) to consider for fall detection

    # Sensitivity as given by the FallDetectionSliderClass instance
    def setFallSensitivity(self, fallingThresholdProportion):
        self.fallingThresholdProportion = fallingThresholdProportion

    # Calculate vertical speed based on height changes
    def calculateSpeed(self, tid, frameTime):
        if len(self.heightBuffer[tid]) < 2 or self.heightBuffer[tid][0] == -5 or self.heightBuffer[tid][1] == -5:
            return 0
        
        # Calculate speed in meters per second
        heightDifference = self.heightBuffer[tid][0] - self.heightBuffer[tid][1]
        timeInterval = 1.0 / (1000.0 / frameTime)  # Convert frameTime from ms to seconds
        return heightDifference / timeInterval

    # Update the fall detection results for every track in the frame
    def step(self, heights, tracks):
        # Decrement results for fall detection display
        for idx, result in enumerate(self.fallBufferDisplay):
            self.fallBufferDisplay[idx] = max(self.fallBufferDisplay[idx] - 1, 0)

        trackIDsInCurrFrame = []
        currentTime = time.time()
        frameTime = 55  # Default frame time in milliseconds (adjust if needed)
        
        # Populate heights for current tracks
        for height in heights:
            # Find track with correct TID
            for track in tracks:
                # Found correct track
                if (int(track[0]) == int(height[0])):
                    tid = int(height[0])
                    self.heightBuffer[tid].appendleft(height[1])
                    trackIDsInCurrFrame.append(tid)
                    
                    # Calculate vertical speed
                    speed = self.calculateSpeed(tid, frameTime)
                    self.speedBuffer[tid].appendleft(speed)
                    
                    # Skip detection if we're in the cooldown period
                    if currentTime - self.lastFallTime[tid] < self.fallCooldownPeriod:
                        continue
                        
                    # Multiple criteria for fall detection
                    height_criterion = self.heightBuffer[tid][0] < self.fallingThresholdProportion * self.heightBuffer[tid][-1]
                    min_height_criterion = self.heightBuffer[tid][-1] > self.minHeightThreshold  # Person must be at least this tall initially
                    speed_criterion = speed < self.maxFallSpeed  # Significant downward movement
                    
                    # Check if all criteria are met
                    if(height_criterion and min_height_criterion and speed_criterion):
                        self.consistentFallFrames[tid] += 1
                        
                        # Only trigger a fall if we have enough consistent frames
                        if self.consistentFallFrames[tid] >= self.requiredConsistentFrames:
                            self.fallBufferDisplay[tid] = self.numFramesToDisplayFall
                            self.lastFallTime[tid] = currentTime
                            self.consistentFallFrames[tid] = 0
                    else:
                        # Reset consistent frame counter if criteria not met
                        self.consistentFallFrames[tid] = 0

        # Reset the buffer for tracks that were detected in the previous frame but not the current frame
        tracksToReset = set(self.tracksIDsInPreviousFrame) - set(trackIDsInCurrFrame) 
        for track in tracksToReset:
            for frame in range(self.heightHistoryLen):
                self.heightBuffer[track].appendleft(-5) # Fill the buffer with -5's to remove any history for the track
                self.speedBuffer[track].appendleft(0) # Reset speed buffer too
            self.consistentFallFrames[track] = 0  # Reset consistent frame counter
            
        self.tracksIDsInPreviousFrame = copy.deepcopy(trackIDsInCurrFrame)
        
        return self.fallBufferDisplay
        
    # def sendFallAlert(self):


# TODO This stuff was never used in original implementation?
#     def resetFallText(self):
#         self.fallAlert.setText('Standing')
#         self.fallPic.setPixmap(self.standingPicture)
#         self.fallResetTimerOn = 0


#     def updateFallThresh(self):
#         try:
#             newThresh = float(self.fallThreshInput.text())
#             self.fallThresh = newThresh
#             self.fallThreshMarker.setPos(self.fallThresh)
#         except:
#             print('No numerical threshold')
