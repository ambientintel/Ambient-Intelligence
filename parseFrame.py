import logging
import struct
import numpy as np
import math

log = logging.getLogger(__name__)

def parseStandardFrame(frameData):
    # Constants for parsing frame header
    headerStruct = 'Q8I'
    frameHeaderLen = struct.calcsize(headerStruct)
    tlvHeaderLength = 8

    # Define the function's output structure and initialize error field to no error
    outputDict = {}
    outputDict['error'] = 0

    # A sum to track the frame packet length for verification for transmission integrity 
    totalLenCheck = 0   

    # Read in frame Header
    try:
        magic, version, totalPacketLen, platform, frameNum, timeCPUCycles, numDetectedObj, numTLVs, subFrameNum = struct.unpack(headerStruct, frameData[:frameHeaderLen])
    except:
        log.error('Error: Could not read frame header')
        outputDict['error'] = 1

    # Move frameData ptr to start of 1st TLV   
    frameData = frameData[frameHeaderLen:]
    totalLenCheck += frameHeaderLen

    # Save frame number to output
    outputDict['frameNum'] = frameNum

    # Initialize the point cloud struct since it is modified by multiple TLV's
    # Each point has the following: X, Y, Z, Doppler, SNR, Noise, Track index
    outputDict['pointCloud'] = np.zeros((numDetectedObj, 7), np.float64)
    # Initialize the track indexes to a value which indicates no track
    outputDict['pointCloud'][:, 6] = 255
    # Find and parse all TLV's
    for i in range(numTLVs):
        try:
            tlvType, tlvLength = tlvHeaderDecode(frameData[:tlvHeaderLength])
            frameData = frameData[tlvHeaderLength:]
            totalLenCheck += tlvHeaderLength
        except:
            log.warning('TLV Header Parsing Failure: Ignored frame due to parsing error')
            outputDict['error'] = 2
            return {}

        # print(tlvType)

        # if (tlvType in parserFunctions):
        #     parserFunctions[tlvType](frameData[:tlvLength], tlvLength, outputDict)
        # elif (tlvType in unusedTLVs):
        #     log.debug("No function to parse TLV type: %d" % (tlvType))
        # else:
        #     log.info("Invalid TLV type: %d" % (tlvType))

        # Move to next TLV
        frameData = frameData[tlvLength:]
        totalLenCheck += tlvLength
    
    # Pad totalLenCheck to the next largest multiple of 32
    # since the device does this to the totalPacketLen for transmission uniformity
    totalLenCheck = 32 * math.ceil(totalLenCheck / 32)

    # Verify the total packet length to detect transmission error that will cause subsequent frames to dropped
    if (totalLenCheck != totalPacketLen):
        log.warning('Frame packet length read is not equal to totalPacketLen in frame header. Subsequent frames may be dropped.')
        outputDict['error'] = 3

    return outputDict

# Decode TLV Header
def tlvHeaderDecode(data):
    tlvType, tlvLength = struct.unpack('2I', data)
    return tlvType, tlvLength