# Fall Detection Algorithm Documentation

## Basic Fall Detection Algorithm (fall_detection.py)

The fall detection algorithm in `fall_detection.py` implements a height-based approach to detect falls by analyzing changes in a person's height over time. Here's a detailed explanation of how it works:

### Algorithm Overview

<img src="https://github.com/user-attachments/assets/529a6133-ef04-4c1e-89a5-6c10876ad110" alt="Overview" style="width:50%; height:auto;">

### Core Components

<img src="https://github.com/user-attachments/assets/3b09ce27-cda9-4195-8077-5b90358346ed" alt="Core Components" style="width:30%; height:auto;">


### Initialization Process

<img src="https://github.com/user-attachments/assets/bc6a5492-aa12-47b0-b8b5-9ea482c23892" alt="Initialization Process" style="width:50%; height:auto;">


The algorithm initializes with the following steps:
1. Calculates the height history buffer length based on frame time and desired history duration
2. Creates circular buffers to store height history for each potential track
3. Initializes fall display buffer to control how long fall alerts are displayed

### Height Data Processing Flow

<img src="https://github.com/user-attachments/assets/1d2b7d38-7eb1-418b-8b9a-5cfbf0004a06" alt="Data Processing" style="width:50%; height:auto;">


### Fall Detection Logic

<img src="https://github.com/user-attachments/assets/3e3abd2b-f19b-46bf-ae40-9424f5a08b28" alt="Alt Text" style="width:50%; height:auto;">


### Algorithm Implementation Details

The algorithm operates on these key principles:

1. **Height Tracking**:
   - Each tracked person is assigned a unique track ID
   - For each track, a circular buffer stores height measurements
   - The buffer length equals `secondsInFallBuffer × frameTime`

2. **Fall Detection Criteria**:
   - A fall is detected when: `current_height < fallingThresholdProportion × historical_height`
   - Default threshold is 0.6 (60% of original height)
   - This ratio compares current height to historical height from 1.5 seconds ago

3. **Buffer Management**:
   - When a track disappears, its buffer is reset to prevent false positives
   - The algorithm maintains a list of active track IDs
   - For tracks not present in current frame, buffers are filled with default values (-5)

### Code Breakdown

```python
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
            self.heightBuffer[track].appendleft(-5) # Fill the buffer with -5's to remove any history
    self.tracksIDsInPreviousFrame = copy.deepcopy(trackIDsInCurrFrame)
    
    return self.fallBufferDisplay
```

### Fall Detection Visualization

```
Standing position:                 ┌─┐             Fall position:             
(height = 1.7m)                    │ │                                   ┌─┐
                                   │ │                                   │ │
                                   │ │                                   │ │
                                   │ │                                   │ │
                                   │ │                                   │ │
                                ┌──┴─┴──┐                             ───┴─┴───
                                │       │                                
                                │       │                                
                                │       │                                
───────────────────────────────┴───────┴────────────────────────────────────────
                          Historical Height = 1.7m               Current Height = 0.3m
                                                                 
                                                                 Ratio = 0.18 < 0.6
                                                                 FALL DETECTED

![ChatGPT Image May 13, 2025, 03_42_53 PM](https://github.com/user-attachments/assets/14a3c3a2-1f0a-4d1a-9836-7f05f4cde6e2)

```

### Sensitivity Configuration

The algorithm's sensitivity can be adjusted by changing the `fallingThresholdProportion` parameter:
- Lower values (e.g., 0.4) make the algorithm less sensitive, requiring a more dramatic height change
- Higher values (e.g., 0.8) make it more sensitive, potentially detecting smaller height changes

### Advantages and Limitations

**Advantages:**
- Simple and computationally efficient
- Works reliably for vertical falls
- Minimal false positives for clear height changes

**Limitations:**
- Cannot detect falls where height doesn't change significantly
- No consideration of movement velocity or acceleration
- No confidence scoring mechanism
- No cooldown period between fall detections

The basic fall detection algorithm provides a reliable foundation for fall detection by focusing on height changes. For more complex scenarios, the enhanced algorithm in `new_fall_detection.py` incorporates additional parameters like velocity and acceleration analysis.


## Enhanced Fall Detection Algorithm (new_fall_detection.py)

The enhanced fall detection algorithm extends the basic approach with additional features to improve accuracy and reduce false positives.

### Enhanced Algorithm Overview

```
+-------------------+    +-------------------+    +-------------------+
|                   |    |                   |    |                   |
| Multi-parameter   |---→| Multi-criteria    |---→| Confidence-based  |
| Data Collection   |    | Analysis          |    | Fall Detection    |
|                   |    |                   |    |                   |
+-------------------+    +-------------------+    +-------------------+
```

### Additional Parameters

```
+----------------------------------------------+
| Enhanced FallDetection Class                 |
+----------------------------------------------+
| New Parameters:                              |
| - velocity_threshold (default: 0.3)          |
| - acc_threshold (default: 0.4)               |
| - min_confidence (default: 0.7)              |
+----------------------------------------------+
| Additional Buffers:                          |
| - velocityBuffer                             |
| - accelerationBuffer                         |
| - positionBuffer                             |
+----------------------------------------------+
| Additional Tracking:                         |
| - fallConfidence                             |
| - lastFallTime                               |
| - fallAlerts                                 |
+----------------------------------------------+
```

### Multi-criteria Detection Logic

The enhanced algorithm analyzes three key parameters:

1. **Height Ratio**: 
   - Similar to the basic algorithm but as one component of the overall detection
   - Contributes 50% to the confidence score

2. **Velocity Analysis**:
   - Calculates vertical velocity between consecutive height measurements  
   - Contributes 30% to the confidence score
   - Negative velocity (downward movement) is key for fall detection

3. **Acceleration Analysis**:
   - Calculates rate of change in velocity
   - Contributes 20% to the confidence score
   - Sudden negative acceleration indicates a fall

### Confidence Scoring

```
┌─────────────────────┐              ┌─────────────────────┐              ┌─────────────────────┐
│                     │              │                     │              │                     │
│  Height Ratio       │──────────────┤   Velocity          │──────────────┤   Acceleration      │
│  Analysis           │              │   Analysis          │              │   Analysis          │
│                     │              │                     │              │                     │
└──────────┬──────────┘              └──────────┬──────────┘              └──────────┬──────────┘
           │                                    │                                     │
           │                                    │                                     │
           │                                    │                                     │
           │                                    │                                     │
           ▼                                    ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                  │
│                                      Confidence Score Calculation                                │
│                                                                                                  │
│  0.5 × height_confidence + 0.3 × velocity_confidence + 0.2 × acceleration_confidence             │
│                                                                                                  │
└────────────────────────────────────────────────────────┬─────────────────────────────────────────┘
                                                         │
                                                         │
                                                         ▼
                                              ┌─────────────────────┐
                                              │                     │
                                              │  Score ≥ Threshold? │
                                              │  (default: 0.7)     │
                                              │                     │
                                              └──────────┬──────────┘
                                                         │
                                                         │
                           ┌───────────────────────────────────────────────────┐
                           │                                                   │
                           ▼                                                   ▼
               ┌─────────────────────┐                             ┌─────────────────────┐
               │                     │                             │                     │
               │         Yes         │                             │         No          │
               │    FALL DETECTED    │                             │   Continue Tracking │
               │                     │                             │                     │
               └─────────────────────┘                             └─────────────────────┘
```

### Cooldown Mechanism

The enhanced algorithm implements a cooldown period to prevent multiple detections of the same fall event:

```
┌─────────────────────┐              ┌─────────────────────┐
│                     │              │                     │
│  Fall Detected      │──────────────┤  Record timestamp   │
│                     │              │                     │
└─────────────────────┘              └──────────┬──────────┘
                                                │
                                                │
                                                ▼
                                     ┌─────────────────────┐
                                     │                     │
                                     │  Block new fall     │
                                     │  detections for     │
                                     │  10 seconds         │
                                     │                     │
                                     └─────────────────────┘
```

### Fall Alert Generation

When a fall is detected, the algorithm generates detailed alerts:

```
┌─────────────────────┐
│                     │
│  Fall Detected      │
│                     │
└──────────┬──────────┘
           │
           │
           ▼
┌─────────────────────┐
│                     │
│  Create Alert with: │
│  - Track ID         │
│  - Timestamp        │
│  - Confidence score │
│  - Position (x,y,z) │
│                     │
└──────────┬──────────┘
           │
           │
           ▼
┌─────────────────────┐
│                     │
│  Log alert and      │
│  store in alerts    │
│  history            │
│                     │
└─────────────────────┘
```

### Implementation of the Detect Fall Method

```python
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
```

### Advantages of the Enhanced Algorithm

1. **Higher Accuracy**: Multi-parameter analysis reduces false positives and improves detection of various fall types

2. **Confidence Scoring**: Provides a measure of certainty for each fall detection

3. **Cooldown Period**: Prevents multiple detections of the same fall event

4. **Position Tracking**: Records the location where the fall occurred

5. **Detailed Alerts**: Generates comprehensive information about each fall event

### Comparison with Basic Algorithm

```
┌────────────────────────────────────────┬───────────────────────────────────────┐
│                                        │                                       │
│       Basic Fall Detection             │      Enhanced Fall Detection          │
│                                        │                                       │
├────────────────────────────────────────┼───────────────────────────────────────┤
│                                        │                                       │
│ • Height-based detection only          │ • Multi-parameter analysis            │
│                                        │   (height, velocity, acceleration)    │
│                                        │                                       │
│ • Binary detection (fall/no fall)      │ • Confidence scoring (0.0-1.0)        │
│                                        │                                       │
│ • No cooldown between detections       │ • 10-second cooldown period           │
│                                        │                                       │
│ • Limited fall information             │ • Detailed fall alerts with position  │
│                                        │   and timestamp                       │
│                                        │                                       │
│ • Simple implementation                │ • More complex but robust             │
│                                        │                                       │
└────────────────────────────────────────┴───────────────────────────────────────┘
```

The enhanced fall detection algorithm provides a more sophisticated approach to fall detection, balancing sensitivity, specificity, and usability while providing rich information about detected fall events. 
