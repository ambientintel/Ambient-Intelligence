from collections import deque
import copy 

class FallDetection:

    # Initialize the class with the default parameters (tested empirically)
    def __init__(self, maxNumTracks = 30, frameTime = 55, fallingThresholdProportion = 0.6, secondsInFallBuffer = 1.5):
        self.fallingThresholdProportion = fallingThresholdProportion
        self.secondsInFallBuffer = secondsInFallBuffer
        self.heightHistoryLen = int(round(self.secondsInFallBuffer * frameTime))
        self.heightBuffer = [deque([-5] *  self.heightHistoryLen, maxlen =  self.heightHistoryLen) for i in range(maxNumTracks)]
        self.tracksIDsInPreviousFrame = []
        self.fallBufferDisplay = [0 for i in range(maxNumTracks)] # Fall results that will be displayed to screen
        self.numFramesToDisplayFall = 100 # How many frames do you want to display a fall on the screen for

    # Sensitivity as given by the FallDetectionSliderClass instance
    def setFallSensitivity(self, fallingThresholdProportion):
        self.fallingThresholdProportion = fallingThresholdProportion

    # Update the fall detection results for every track in the frame
    def step(self, heights, tracks):
        # Decrement results for fall detection display
        for idx, result in enumerate(self.fallBufferDisplay):
            self.fallBufferDisplay[idx] = max(self.fallBufferDisplay[idx] - 1, 0)

        trackIDsInCurrFrame = []
        # Populate heights for current tracks
        for height in heights:
            # Find track with correct TID
            for track in tracks:
                # Found correct track
                if (int(track[0]) == int(height[0])):
                    tid = int(height[0])
                    self.heightBuffer[tid].appendleft(height[1])
                    trackIDsInCurrFrame.append(tid)
                    
                    # Check if fallen
                    if(self.heightBuffer[tid][0] < self.fallingThresholdProportion * self.heightBuffer[tid][-1]):
                        self.fallBufferDisplay[tid] = self.numFramesToDisplayFall


        # Reset the buffer for tracks that were detected in the previous frame but not the current frame
        tracksToReset = set(self.tracksIDsInPreviousFrame) - set(trackIDsInCurrFrame) 
        for track in tracksToReset:
            for frame in range(self.heightHistoryLen):
                self.heightBuffer[track].appendleft(-5) # Fill the buffer with -5's to remove any history for the track
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
