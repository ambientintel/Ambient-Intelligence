from collections import deque
import copy
import numpy as np

class FallDetection:
    def __init__(self, maxNumTracks=30, frameTime=55, fallingThresholdProportion=0.9, secondsInFallBuffer=2.5):
        self.fallingThresholdProportion = fallingThresholdProportion
        self.secondsInFallBuffer = secondsInFallBuffer
        self.heightHistoryLen = int(round(self.secondsInFallBuffer * frameTime))
        self.heightBuffer = {}  # Use a dictionary instead of a list to handle any track ID
        self.velocityBuffer = {}  # Track vertical velocity
        self.tracksIDsInPreviousFrame = []
        self.fallBufferDisplay = {}  # Fall results that will be displayed to screen
        self.numFramesToDisplayFall = 100
        self.minTrackHistory = 10  # Minimum number of frames to track before detecting falls
        self.heightThreshold = 0.5  # Absolute height threshold in meters
        self.velocityThreshold = -0.5  # Velocity threshold in meters/second
        self.frameTime = frameTime / 1000.0  # Convert to seconds
        
    def setFallSensitivity(self, fallingThresholdProportion):
        self.fallingThresholdProportion = fallingThresholdProportion

    def step(self, heights, tracks):
        # Decrement fall display counters
        for tid in list(self.fallBufferDisplay.keys()):
            self.fallBufferDisplay[tid] = max(self.fallBufferDisplay[tid] - 1, 0)
            
        trackIDsInCurrFrame = []
        
        # Process current tracks
        for height in heights:
            tid = int(height[0])
            current_height = height[1]
            
            # Initialize buffer for new tracks
            if tid not in self.heightBuffer:
                self.heightBuffer[tid] = deque([current_height] * self.heightHistoryLen, 
                                             maxlen=self.heightHistoryLen)
                self.velocityBuffer[tid] = deque([0] * self.heightHistoryLen, 
                                               maxlen=self.heightHistoryLen)
                self.fallBufferDisplay[tid] = 0
            
            # Calculate velocity (change in height / time)
            prev_height = self.heightBuffer[tid][0]
            velocity = (current_height - prev_height) / self.frameTime
            
            # Update buffers
            self.heightBuffer[tid].appendleft(current_height)
            self.velocityBuffer[tid].appendleft(velocity)
            trackIDsInCurrFrame.append(tid)
            
            # Only analyze tracks with sufficient history
            if len(trackIDsInCurrFrame) >= self.minTrackHistory:
                # Get recent height and velocity patterns
                recent_heights = list(self.heightBuffer[tid])[:10]  # Last 10 frames
                recent_velocities = list(self.velocityBuffer[tid])[:10]  # Last 10 frames
                
                # Calculate statistics
                max_height = max(recent_heights)
                min_height = min(recent_heights)
                height_drop = max_height - min_height
                avg_velocity = sum(recent_velocities) / len(recent_velocities)
                min_velocity = min(recent_velocities)
                
                # Multi-factor fall detection
                is_falling = (
                    # Significant height drop relative to maximum height
                    height_drop > self.fallingThresholdProportion * max_height and
                    # Current height is below threshold
                    current_height < self.heightThreshold and
                    # Velocity indicates rapid downward movement
                    min_velocity < self.velocityThreshold
                )
                
                if is_falling:
                    self.fallBufferDisplay[tid] = self.numFramesToDisplayFall
        
        # Handle tracks that disappeared
        tracksToReset = set(self.tracksIDsInPreviousFrame) - set(trackIDsInCurrFrame)
        for tid in tracksToReset:
            if tid in self.heightBuffer:
                self.heightBuffer[tid].clear()
                self.velocityBuffer[tid].clear()
        
        self.tracksIDsInPreviousFrame = copy.deepcopy(trackIDsInCurrFrame)
        
        # Return results in the expected format (list indexed by track ID)
        result = [0] * max(list(self.fallBufferDisplay.keys()) + [0]) + [1]
        for tid, value in self.fallBufferDisplay.items():
            if tid < len(result):
                result[tid] = value
                
        return result