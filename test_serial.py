#!/usr/bin/env python3

"""
Test script to verify PySerial imports and list available COM ports
"""

import sys
import platform

print(f"Python version: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")

try:
    import serial
    print("Successfully imported serial module")
    print(f"Serial version: {serial.__version__}")
    
    try:
        from serial.tools import list_ports
        print("Successfully imported serial.tools.list_ports")
        
        ports = list(list_ports.comports())
        print(f"Found {len(ports)} ports:")
        for i, port in enumerate(ports):
            print(f"  [{i+1}] {port.device}: {port.description}")
            
    except ImportError as e:
        print(f"Error importing serial.tools.list_ports: {e}")
        
except ImportError as e:
    print(f"Error importing serial module: {e}")
    
print("Test complete") 