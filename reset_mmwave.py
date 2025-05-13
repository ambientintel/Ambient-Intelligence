#!/usr/bin/env python3
"""
Reset utility for TI IWR6843_AoP 60Hz mmWave Radar

This script provides a simple command-line interface to reset the radar
using both hardware and software methods.

Usage:
  python reset_mmwave.py [--cli-port COM_PORT] [--data-port COM_PORT] [--method METHOD]
  
  Options:
    --cli-port     Optional COM port for CLI commands
    --data-port    Optional COM port for data
    --method       Reset method: 'full', 'hw', 'sw', or 'specialized' (default: 'full')
    --list         List available COM ports
"""

import sys
import argparse
import logging
import time
import os
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import serial for COM port detection directly
try:
    import serial
    from serial.tools import list_ports
    HAS_SERIAL = True
except ImportError:
    logger.warning("PySerial not installed. COM port auto-detection will be limited.")
    HAS_SERIAL = False

# Import our radar reset functionality
try:
    from radar_reset import (
        reset_radar, 
        hardware_reset_radar, 
        software_reset_radar, 
        reset_iwr6843_aop_60hz,
        HAS_PYFTDI as RADAR_HAS_PYFTDI
    )
    HAS_RADAR_RESET = True
except ImportError:
    logger.error("radar_reset module not available.")
    HAS_RADAR_RESET = False
    RADAR_HAS_PYFTDI = False

# Known descriptors for CLI and Data ports for mmWave radar
CLI_PORT_DESCRIPTORS = ['Enhanced COM Port', 'Application/User UART', 'XDS110', 'User UART']
DATA_PORT_DESCRIPTORS = ['Standard COM Port', 'Auxiliary Data Port', 'XDS110']

def list_com_ports():
    """List available COM ports and try to identify radar ports"""
    if not HAS_SERIAL:
        logger.error("PySerial not installed. Cannot list COM ports.")
        return None, None
    
    try:
        serialPorts = list(list_ports.comports())
        logger.info(f"Found {len(serialPorts)} COM ports:")
        
        cli_port = None
        data_port = None
        
        for i, port in enumerate(serialPorts):
            logger.info(f"  [{i+1}] {port.device}: {port.description}")
            
            # Try to identify CLI and Data ports
            for desc in CLI_PORT_DESCRIPTORS:
                if desc.lower() in port.description.lower() and not cli_port:
                    cli_port = port.device
                    logger.info(f"    Possible CLI port for radar")
                    
            for desc in DATA_PORT_DESCRIPTORS:
                if desc.lower() in port.description.lower() and not data_port:
                    data_port = port.device
                    logger.info(f"    Possible Data port for radar")
        
        if cli_port:
            logger.info(f"Detected CLI port: {cli_port}")
        if data_port:
            logger.info(f"Detected Data port: {data_port}")
            
        return cli_port, data_port
    except Exception as e:
        logger.error(f"Error listing COM ports: {e}")
        return None, None

def detect_com_ports():
    """Detect available COM ports and identify radar ports"""
    system = platform.system()
    cli_port = None
    data_port = None
    
    if system == "Linux":
        # Linux often uses these device names for mmWave radar
        if os.path.exists('/dev/ttyUSB0'):
            cli_port = '/dev/ttyUSB0'
        if os.path.exists('/dev/ttyUSB1'):
            data_port = '/dev/ttyUSB1'
            
    elif system == "Windows":
        # On Windows, use serial.tools.list_ports to find the ports
        cli_port, data_port = list_com_ports()
    
    return cli_port, data_port

def verify_com_ports(cli_port, data_port):
    """Verify that the COM ports actually exist"""
    if not cli_port or not data_port:
        return False
        
    if platform.system() == "Windows":
        cli_exists = cli_port.startswith("COM")
        data_exists = data_port.startswith("COM")
    else:  # Linux/macOS
        cli_exists = os.path.exists(cli_port)
        data_exists = os.path.exists(data_port)
        
    return cli_exists and data_exists

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Reset TI IWR6843_AoP 60Hz mmWave Radar')
    parser.add_argument('--cli-port', dest='cli_port', help='COM port for CLI commands')
    parser.add_argument('--data-port', dest='data_port', help='COM port for data')
    parser.add_argument('--method', dest='method', choices=['full', 'hw', 'sw', 'specialized'],
                       default='full', help='Reset method (default: full)')
    parser.add_argument('--list', dest='list_ports', action='store_true',
                       help='List available COM ports and exit')
    parser.add_argument('--force', dest='force', action='store_true',
                       help='Force reset even if COM ports are not detected')
    return parser.parse_args()

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_arguments()
    
    # List ports if requested
    if args.list_ports:
        cli_port, data_port = list_com_ports()
        if cli_port or data_port:
            logger.info("Detected radar COM ports:")
            if cli_port:
                logger.info(f"  CLI port: {cli_port}")
            if data_port:
                logger.info(f"  Data port: {data_port}")
        return 0
    
    # Check dependencies before proceeding with reset
    if not HAS_RADAR_RESET:
        logger.error("radar_reset module not available. Please ensure the file is in the same directory.")
        return 1
        
    if not RADAR_HAS_PYFTDI:
        logger.error("PyFTDI not available. Please install it using: pip install pyftdi")
        return 1
    
    # Determine COM ports (from args or auto-detect)
    cli_port = args.cli_port
    data_port = args.data_port
    
    if not (cli_port and data_port):
        logger.info("COM ports not specified, attempting to auto-detect...")
        detected_cli, detected_data = detect_com_ports()
        
        if not cli_port:
            cli_port = detected_cli
        if not data_port:
            data_port = detected_data
            
    # Verify ports exist
    if not verify_com_ports(cli_port, data_port) and not args.force:
        logger.error(f"Unable to verify COM ports (CLI: {cli_port}, Data: {data_port})")
        logger.error("Please specify valid COM ports or use --force to override")
        return 1
        
    logger.info(f"Using CLI port: {cli_port}, Data port: {data_port}")
    logger.info(f"Starting radar reset with method: {args.method}")
    
    success = False
    
    # Perform the requested reset method
    try:
        if args.method == 'full':
            success = reset_radar()
        elif args.method == 'hw':
            success = hardware_reset_radar()
        elif args.method == 'sw':
            success = software_reset_radar(cli_port, data_port)
        elif args.method == 'specialized':
            success = reset_iwr6843_aop_60hz(cli_port, data_port)
    except Exception as e:
        logger.error(f"Error during radar reset: {e}")
        return 1
    
    # Report result
    if success:
        logger.info("Radar reset completed successfully")
        logger.info("Waiting 3 seconds for radar to fully initialize...")
        time.sleep(3)
        logger.info("Radar should now be ready for use")
        return 0
    else:
        logger.error("Radar reset failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 