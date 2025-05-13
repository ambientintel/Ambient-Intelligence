"""
Radar Reset Module for TI IWR6843_AoP 60Hz mmWave Radar
Uses PyFTDI to perform a hardware reset of the radar device
"""

import time
import logging
import sys
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try importing PyFTDI
try:
    from pyftdi.ftdi import Ftdi
    from pyftdi.serialext import SerialPort
    HAS_PYFTDI = True
except ImportError:
    logger.warning("PyFTDI not available. Hardware reset will not be possible.")
    HAS_PYFTDI = False

# Make sure HAS_PYFTDI is exported
__all__ = [
    'reset_radar',
    'hardware_reset_radar',
    'software_reset_radar',
    'reset_iwr6843_aop_60hz',
    'HAS_PYFTDI'
]

# FTDI device identifiers for TI IWR6843_AoP radar
# These are standard values, may need adjustment for your specific hardware
FTDI_VENDOR_ID = 0x0451  # TI vendor ID
FTDI_PRODUCT_ID = 0xbef3  # IWR6843 product ID (may vary)
FTDI_DESCRIPTION = "XDS110 Class Application/User UART"  # Common for TI mmWave devices

# Additional identifiers specific to IWR6843_AoP 60Hz variant
IWR6843_AOP_DESCRIPTIONS = [
    "XDS110 Class Application/User UART",
    "XDS110",
    "User UART",
    "TI IWR6843",
    "Enhanced COM Port"
]

def find_ftdi_device() -> Optional[Tuple[str, str]]:
    """
    Find the FTDI device connected to the IWR6843 radar.
    
    Returns:
        Tuple of (CLI port URL, Data port URL) if found, None otherwise
    """
    if not HAS_PYFTDI:
        logger.error("PyFTDI not available. Cannot find FTDI device.")
        return None
    
    try:
        # Get available FTDI devices
        available_devices = Ftdi.list_devices()
        logger.info(f"Found {len(available_devices)} FTDI devices")
        
        # Filter for likely TI IWR6843 devices
        radar_devices = []
        for device in available_devices:
            device_info = device[0]
            # Check if vendor ID matches or description contains known patterns
            if (device_info.vid == FTDI_VENDOR_ID):
                radar_devices.append(device_info)
                logger.info(f"Found TI device by vendor ID: {device_info.description}")
            else:
                # Check if description matches any known patterns
                for desc in IWR6843_AOP_DESCRIPTIONS:
                    if desc.lower() in device_info.description.lower():
                        radar_devices.append(device_info)
                        logger.info(f"Found potential radar device: {device_info.description}")
                        break
        
        if not radar_devices:
            logger.error("No TI IWR6843 radar devices found")
            return None
            
        # Get port URLs for CLI and data ports
        # IWR6843 typically has two ports - one for CLI commands and one for data
        if len(radar_devices) >= 2:
            # Assuming first port is CLI and second is data
            cli_port = f"ftdi://{radar_devices[0].vid:04x}:{radar_devices[0].pid:04x}/1"
            data_port = f"ftdi://{radar_devices[1].vid:04x}:{radar_devices[1].pid:04x}/1"
            return cli_port, data_port
        elif len(radar_devices) == 1:
            # Single device with possibly multiple interfaces
            cli_port = f"ftdi://{radar_devices[0].vid:04x}:{radar_devices[0].pid:04x}/1"
            data_port = f"ftdi://{radar_devices[0].vid:04x}:{radar_devices[0].pid:04x}/2"
            return cli_port, data_port
        else:
            logger.error("Could not determine CLI and Data ports for the radar")
            return None
    
    except Exception as e:
        logger.error(f"Error finding FTDI device: {e}")
        return None

def hardware_reset_radar() -> bool:
    """
    Perform a hardware reset of the IWR6843 radar using FTDI control signals.
    This uses the FTDI chip's ability to toggle hardware control lines.
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    if not HAS_PYFTDI:
        logger.error("PyFTDI not available. Cannot perform hardware reset.")
        return False
        
    try:
        # Find the radar device
        port_urls = find_ftdi_device()
        if not port_urls:
            logger.error("Could not find FTDI device for radar. Hardware reset failed.")
            return False
            
        cli_port_url, _ = port_urls
        
        logger.info(f"Attempting hardware reset using CLI port: {cli_port_url}")
        
        # Open connection to the FTDI device
        ftdi = Ftdi()
        ftdi.open_from_url(cli_port_url)
        
        # Toggle DTR and RTS pins to reset the device
        # DTR (Data Terminal Ready) is often used for hardware reset
        logger.info("Asserting DTR line (low)")
        ftdi.set_dtr(False)  # Assert DTR (active low)
        time.sleep(0.5)
        
        logger.info("De-asserting DTR line (high)")
        ftdi.set_dtr(True)   # De-assert DTR
        time.sleep(1.0)      # Give device time to reset
        
        # Additionally toggle RTS (Request To Send) which can help with reset on some hardware
        logger.info("Toggling RTS line")
        ftdi.set_rts(False)
        time.sleep(0.2)
        ftdi.set_rts(True)
        time.sleep(0.5)
        
        # Close the FTDI connection
        ftdi.close()
        logger.info("Hardware reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during hardware reset: {e}")
        return False

def software_reset_radar(cli_port=None, data_port=None) -> bool:
    """
    Perform a software reset of the radar by sending specific commands.
    
    Args:
        cli_port: Serial port for CLI commands
        data_port: Serial port for data
        
    Returns:
        bool: True if reset was successful, False otherwise
    """
    if not HAS_PYFTDI:
        logger.error("PyFTDI not available. Cannot perform software reset.")
        return False
        
    try:
        # Find the radar device if ports not provided
        if not cli_port or not data_port:
            port_urls = find_ftdi_device()
            if not port_urls:
                logger.error("Could not find FTDI device for radar. Software reset failed.")
                return False
            cli_port_url, data_port_url = port_urls
        else:
            # Convert regular serial ports to FTDI URLs
            cli_port_url = f"ftdi://:{cli_port}/"
            data_port_url = f"ftdi://:{data_port}/"
        
        logger.info(f"Attempting software reset using CLI port: {cli_port_url}")
        
        # Open serial connection using PyFTDI
        serial_port = SerialPort(cli_port_url, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1)
        
        # Send reset commands
        commands = [
            "sensorStop\n",
            "flushCfg\n", 
            "reset\n"
        ]
        
        for cmd in commands:
            logger.info(f"Sending command: {cmd.strip()}")
            serial_port.write(cmd.encode())
            time.sleep(0.5)
            response = serial_port.read(256)
            if response:
                logger.info(f"Response: {response.decode(errors='ignore').strip()}")
        
        # Close the connection
        serial_port.close()
        logger.info("Software reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during software reset: {e}")
        return False

def reset_iwr6843_aop_60hz(cli_port=None, data_port=None) -> bool:
    """
    Specialized reset function specifically for the TI IWR6843_AoP 60Hz mmWave radar.
    This uses a combination of hardware and software reset methods optimized for this device.
    
    Args:
        cli_port: Optional CLI COM port (if known)
        data_port: Optional Data COM port (if known)
        
    Returns:
        bool: True if reset was successful, False otherwise
    """
    logger.info("Starting specialized reset for IWR6843_AoP 60Hz mmWave radar")
    
    if not HAS_PYFTDI:
        logger.warning("PyFTDI not available. Cannot perform specialized reset.")
        return False
    
    try:
        # Step 1: Hardware reset
        hw_success = hardware_reset_radar()
        if not hw_success:
            logger.warning("Hardware reset step failed")
        
        # Wait between reset steps
        time.sleep(1.5)
        
        # Step 2: Find ports (or use provided ones)
        if not cli_port or not data_port:
            port_urls = find_ftdi_device()
            if not port_urls:
                logger.error("Could not find FTDI device ports")
                return False
            cli_port_url, data_port_url = port_urls
        else:
            # Convert regular serial ports to FTDI URLs
            cli_port_url = f"ftdi://:{cli_port}/"
            data_port_url = f"ftdi://:{data_port}/"
            
        # Step 3: Send IWR6843 specific reset sequence
        logger.info("Sending IWR6843 specific reset sequence")
        serial_port = SerialPort(cli_port_url, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1)
        
        # IWR6843 60Hz specific reset sequence
        iwr6843_commands = [
            "sensorStop\n",
            "flushCfg\n",
            "reset\n",
            # Wait longer after reset command
            # Additional commands can be added here if needed for 60Hz IWR6843
        ]
        
        for cmd in iwr6843_commands:
            logger.info(f"Sending command: {cmd.strip()}")
            serial_port.write(cmd.encode())
            # Extended delay for reset command
            if cmd.strip() == "reset":
                time.sleep(2.0)
            else:
                time.sleep(0.5)
                
            response = serial_port.read(256)
            if response:
                logger.info(f"Response: {response.decode(errors='ignore').strip()}")
        
        # Close connection
        serial_port.close()
        
        logger.info("IWR6843_AoP 60Hz reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during IWR6843_AoP 60Hz reset: {e}")
        return False

def reset_radar() -> bool:
    """
    Complete radar reset using both hardware and software methods.
    This function will try to use the specialized IWR6843_AoP reset first,
    and fall back to generic methods if that fails.
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    logger.info("Starting complete radar reset sequence")
    
    # Try specialized IWR6843_AoP reset first
    success = reset_iwr6843_aop_60hz()
    if success:
        return True
        
    logger.warning("Specialized reset failed, trying generic reset methods")
    
    # Try hardware reset
    hw_success = hardware_reset_radar()
    if not hw_success:
        logger.warning("Hardware reset failed or unavailable, will try software reset")
    
    # Wait a bit between reset methods
    time.sleep(1.0)
    
    # Always do software reset after hardware reset
    sw_success = software_reset_radar()
    
    # Return overall success (both should ideally succeed, but one is better than none)
    return hw_success or sw_success

if __name__ == "__main__":
    success = reset_radar()
    sys.exit(0 if success else 1) 