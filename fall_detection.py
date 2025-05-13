from collections import deque
import copy
import numpy as np
import time

class FallDetection:

    # Initialize the class with the default parameters 
    def __init__(self, maxNumTracks=30, frameTime=55, fallingThresholdProportion=0.6, 
                 secondsInFallBuffer=1.5, velocity_threshold=0.3, 
                 acc_threshold=0.4, min_confidence=0.7):
        # Core parameters
        self.fallingThresholdProportion = fallingThresholdProportion
        self.velocity_threshold = velocity_threshold
        self.acc_threshold = acc_threshold
        self.min_confidence = min_confidence
        self.secondsInFallBuffer = secondsInFallBuffer
        
        # Buffer setup
        self.heightHistoryLen = int(round(self.secondsInFallBuffer * frameTime))
        self.heightBuffer = [deque([-5] * self.heightHistoryLen, maxlen=self.heightHistoryLen) for i in range(maxNumTracks)]
        self.velocityBuffer = [deque([0] * self.heightHistoryLen, maxlen=self.heightHistoryLen) for i in range(maxNumTracks)]
        self.accelerationBuffer = [deque([0] * self.heightHistoryLen, maxlen=self.heightHistoryLen) for i in range(maxNumTracks)]
        self.positionBuffer = [deque([(0, 0, 0)] * self.heightHistoryLen, maxlen=self.heightHistoryLen) for i in range(maxNumTracks)]
        
        # Tracking and display
        self.tracksIDsInPreviousFrame = []
        self.fallBufferDisplay = [0 for i in range(maxNumTracks)]  # Fall results that will be displayed to screen
        self.numFramesToDisplayFall = 100  # How many frames to display a fall on the screen
        
        # Fall confidence tracking
        self.fallConfidence = [0.0 for i in range(maxNumTracks)]
        self.lastFallTime = [0 for i in range(maxNumTracks)]
        self.cooldownPeriod = 10  # seconds between possible repeated fall detections
        
        # Fall alerts
        self.fallAlerts = []  # Store fall alert information
        self.alertSent = [False for i in range(maxNumTracks)]

    # Sensitivity as given by the FallDetectionSliderClass instance
    def setFallSensitivity(self, fallingThresholdProportion):
        self.fallingThresholdProportion = fallingThresholdProportion
        
    def setVelocityThreshold(self, velocity_threshold):
        self.velocity_threshold = velocity_threshold
        
    def setAccelerationThreshold(self, acc_threshold):
        self.acc_threshold = acc_threshold
        
    def setMinConfidence(self, min_confidence):
        self.min_confidence = min_confidence

    # Calculate velocity between two height points
    def calculate_velocity(self, h1, h2):
        if h1 == -5 or h2 == -5:  # Invalid height values
            return 0
        return h1 - h2  # Simple velocity calculation
    
    # Calculate acceleration between velocity points
    def calculate_acceleration(self, v1, v2):
        return v1 - v2  # Simple acceleration calculation

    # Check if a fall is detected based on multiple criteria
    def detect_fall(self, tid):
        # Height-based criterion (original)
        height_ratio = 0
        if self.heightBuffer[tid][-1] > 0 and self.heightBuffer[tid][0] > 0:
            height_ratio = self.heightBuffer[tid][0] / max(self.heightBuffer[tid][-1], 0.1)
        height_criterion = height_ratio < self.fallingThresholdProportion
        
        # Velocity-based criterion
        velocity_values = list(self.velocityBuffer[tid])
        velocity_criterion = False
        if any(velocity_values) and min(velocity_values) != -5:
            max_velocity = min(velocity_values)  # min because negative velocity means downward movement
            velocity_criterion = max_velocity < -self.velocity_threshold
        
        # Acceleration-based criterion
        acc_values = list(self.accelerationBuffer[tid])
        acc_criterion = False
        if any(acc_values):
            max_acc = min(acc_values)  # Sudden negative acceleration
            acc_criterion = max_acc < -self.acc_threshold
            
        # Calculate confidence score (weighted combination)
        confidence = 0.0
        if height_criterion:
            confidence += 0.5 * (1 - height_ratio/self.fallingThresholdProportion)
            
        if velocity_criterion:
            max_velocity = min(velocity_values) if any(velocity_values) and min(velocity_values) != -5 else 0
            confidence += 0.3 * min(1.0, abs(max_velocity) / self.velocity_threshold)
            
        if acc_criterion:
            max_acc = min(acc_values) if any(acc_values) else 0
            confidence += 0.2 * min(1.0, abs(max_acc) / self.acc_threshold)
            
        # Check for overall confidence threshold
        is_fall = confidence >= self.min_confidence
        
        # Cooldown period check
        current_time = time.time()
        if current_time - self.lastFallTime[tid] < self.cooldownPeriod:
            is_fall = False
            
        # Update fall confidence
        self.fallConfidence[tid] = confidence
        
        # Record fall time if detected
        if is_fall:
            self.lastFallTime[tid] = current_time
            
        return is_fall, confidence

    # Update the fall detection results for every track in the frame
    def step(self, heights, tracks, positions=None):
        # Decrement results for fall detection display
        for idx, result in enumerate(self.fallBufferDisplay):
            self.fallBufferDisplay[idx] = max(self.fallBufferDisplay[idx] - 1, 0)

        trackIDsInCurrFrame = []
        # Populate heights for current tracks
        for i, height in enumerate(heights):
            # Find track with correct TID
            for track in tracks:
                # Found correct track
                if (int(track[0]) == int(height[0])):
                    tid = int(height[0])
                    
                    # Store height
                    prev_height = self.heightBuffer[tid][0] if len(self.heightBuffer[tid]) > 0 else -5
                    self.heightBuffer[tid].appendleft(height[1])
                    
                    # Calculate and store velocity
                    velocity = self.calculate_velocity(height[1], prev_height)
                    self.velocityBuffer[tid].appendleft(velocity)
                    
                    # Calculate and store acceleration
                    prev_velocity = self.velocityBuffer[tid][1] if len(self.velocityBuffer[tid]) > 1 else 0
                    acceleration = self.calculate_acceleration(velocity, prev_velocity)
                    self.accelerationBuffer[tid].appendleft(acceleration)
                    
                    # Store position if available
                    if positions and i < len(positions):
                        self.positionBuffer[tid].appendleft(positions[i])
                    
                    trackIDsInCurrFrame.append(tid)
                    
                    # Check if fallen using multiple criteria
                    is_fall, confidence = self.detect_fall(tid)
                    if is_fall:
                        self.fallBufferDisplay[tid] = self.numFramesToDisplayFall
                        if not self.alertSent[tid]:
                            self.sendFallAlert(tid, confidence)
                            self.alertSent[tid] = True
                    else:
                        self.alertSent[tid] = False

        # Reset the buffer for tracks that were detected in the previous frame but not the current frame
        tracksToReset = set(self.tracksIDsInPreviousFrame) - set(trackIDsInCurrFrame) 
        for track in tracksToReset:
            for frame in range(self.heightHistoryLen):
                self.heightBuffer[track].appendleft(-5)  # Fill the buffer with -5's to remove any history
                self.velocityBuffer[track].appendleft(0)
                self.accelerationBuffer[track].appendleft(0)
                self.positionBuffer[track].appendleft((0, 0, 0))
                
        self.tracksIDsInPreviousFrame = copy.deepcopy(trackIDsInCurrFrame)
        
        return self.fallBufferDisplay
        
    def sendFallAlert(self, tid, confidence):
        """
        Send a fall alert with details about the detected fall
        
        Args:
            tid: Track ID of the person who fell
            confidence: Confidence score for the fall detection
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        alert = {
            "track_id": tid,
            "timestamp": timestamp,
            "confidence": confidence,
            "position": self.positionBuffer[tid][0] if len(self.positionBuffer[tid]) > 0 else (0, 0, 0)
        }
        self.fallAlerts.append(alert)
        # Implementation to send the alert via notification system, email, etc. would go here
        print(f"FALL DETECTED - Track ID: {tid}, Confidence: {confidence:.2f}, Time: {timestamp}")
        
    def getFallAlerts(self):
        """
        Get the list of all fall alerts recorded
        """
        return self.fallAlerts


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
