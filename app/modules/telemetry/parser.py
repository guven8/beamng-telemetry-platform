"""
OutGauge protocol parser for BeamNG.drive telemetry packets.

Parses binary UDP packets from BeamNG's OutGauge output into structured TelemetrySample objects.
This is a minimal implementation that handles the core OutGauge fields we need.

BeamNG Compatibility:
- BeamNG can output multiple UDP protocols on the same port (OutGauge + MotionSim)
- MotionSim packets start with ASCII "BNG1" (4 bytes) - used for motion rigs, not dashboards
- We detect and ignore MotionSim packets to prevent misparsing
- Reference: BeamNG.drive documentation on UDP telemetry protocols
"""
import struct
import logging
from datetime import datetime, timezone
from app.modules.telemetry.schemas import TelemetrySample

logger = logging.getLogger(__name__)

# MotionSim protocol header (BeamNG motion rig protocol)
# MotionSim packets start with "BNG1" to allow receivers to distinguish from OutGauge
MOTIONSIM_HEADER = b"BNG1"

# OutGauge packet structure (standard format)
# Based on OutGauge protocol specification
# Packet is 96 bytes total
OUTGAUGE_PACKET_SIZE = 96
# Format: Time(4) + Car(4) + Flags(2) + Gear(1) + PLID(1) + Speed(4) + RPM(4) + 
#         Turbo(4) + EngTemp(4) + Fuel(4) + OilPressure(4) + OilTemp(4) +
#         DashLights(4) + ShowLights(4) + Throttle(4) + Brake(4) + Clutch(4) +
#         Display1(12) + Display2(12) + ID(4)
# Total: 4+4+2+1+1+4*7+4*2+4*3+12+12+4 = 96 bytes
# Note: Using 'c' for gear (char) and Display fields are 12 bytes each
OUTGAUGE_STRUCT_FORMAT = "<I4sHcBffffffffIIffff12s12si"


def parse_outgauge_packet(data: bytes) -> TelemetrySample | None:
    """
    Parse an OutGauge protocol UDP packet into a TelemetrySample.
    
    Handles BeamNG's multi-protocol UDP output by detecting and ignoring MotionSim packets.
    Only processes OutGauge packets that match the expected 96-byte structure.
    
    OutGauge packet structure (little-endian):
    - Time: 4 bytes (unsigned int)
    - Car: 4 bytes (char[4])
    - Flags: 2 bytes (unsigned short)
    - Gear: 1 byte (char, 'R' = reverse, 'N' = neutral, '0'-'9' = gear)
    - PLID: 1 byte (unsigned char)
    - Speed: 4 bytes (float, m/s)
    - RPM: 4 bytes (float)
    - Turbo: 4 bytes (float)
    - EngTemp: 4 bytes (float)
    - Fuel: 4 bytes (float)
    - OilPressure: 4 bytes (float)
    - OilTemp: 4 bytes (float)
    - DashLights: 4 bytes (unsigned int)
    - ShowLights: 4 bytes (unsigned int)
    - Throttle: 4 bytes (float, 0.0-1.0)
    - Brake: 4 bytes (float, 0.0-1.0)
    - Clutch: 4 bytes (float, 0.0-1.0)
    - Display1: 12 bytes (char[12])
    - Display2: 12 bytes (char[12])
    - ID: 4 bytes (int)
    
    Args:
        data: Raw UDP packet bytes
        
    Returns:
        TelemetrySample if parsing succeeds, None if packet is invalid or ignored
    """
    try:
        # Check for MotionSim protocol header (BNG1)
        # BeamNG uses this header so receivers can ignore MotionSim packets when both
        # protocols share the same port (common default configuration)
        if len(data) >= 4 and data.startswith(MOTIONSIM_HEADER):
            logger.debug("Ignoring MotionSim packet (BNG1 header detected)")
            return None
        
        # Only parse OutGauge packets that match the expected size exactly
        # OutGauge packets are always 96 bytes - other sizes are invalid or different protocols
        if len(data) != OUTGAUGE_PACKET_SIZE:
            # Don't log every mismatch to avoid spam (only log occasionally)
            if not hasattr(parse_outgauge_packet, '_size_warn_count'):
                parse_outgauge_packet._size_warn_count = 0
            if parse_outgauge_packet._size_warn_count < 3:
                logger.debug(f"Ignoring packet with unexpected size: {len(data)} bytes (expected {OUTGAUGE_PACKET_SIZE})")
                parse_outgauge_packet._size_warn_count += 1
            return None
        
        # Validate minimum packet size (should already be 96, but double-check)
        if len(data) < 20:  # Minimum size for core fields
            logger.warning(f"Packet too small: {len(data)} bytes")
            return None
        
        # Parse as full OutGauge packet (we've already validated it's exactly 96 bytes)
        unpacked = struct.unpack(OUTGAUGE_STRUCT_FORMAT, data[:OUTGAUGE_PACKET_SIZE])
        
        # Extract fields
        _time = unpacked[0]
        _car = unpacked[1]
        _flags = unpacked[2]
        gear_char = unpacked[3]
        _plid = unpacked[4]
        speed = unpacked[5]  # m/s
        rpm_float = unpacked[6]
        
        # Debug: log gear_char to understand what we're getting
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Raw gear_char: {repr(gear_char)}, type: {type(gear_char)}")
        _turbo = unpacked[7]
        _eng_temp = unpacked[8]
        _fuel = unpacked[9]
        _oil_pressure = unpacked[10]
        _oil_temp = unpacked[11]
        _dash_lights = unpacked[12]
        _show_lights = unpacked[13]
        throttle = unpacked[14]
        brake = unpacked[15]
        _clutch = unpacked[16]
        _display1 = unpacked[17]
        _display2 = unpacked[18]
        _id = unpacked[19]
        
        # Convert gear character to integer
        # With 'c' format, gear_char is a bytes object of length 1
        gear = None
        gear_byte = None
        
        if isinstance(gear_char, bytes):
            if len(gear_char) > 0:
                gear_byte = gear_char[0]
            else:
                gear_byte = 0
        elif isinstance(gear_char, str):
            if len(gear_char) > 0:
                gear_byte = ord(gear_char[0])
            else:
                gear_byte = 0
        elif isinstance(gear_char, int):
            gear_byte = gear_char
        else:
            gear_byte = 0
            logger.warning(f"Unexpected gear_char type: {type(gear_char)}, value: {repr(gear_char)}")
        
        # Parse gear value
        # BeamNG.drive uses 1-indexed numeric values: 1=neutral, 2=gear1, 3=gear2, etc.
        # We convert to 0-indexed: 0=neutral, 1=gear1, 2=gear2, -1=reverse
        # Some implementations use ASCII chars ('R', 'N', '0'-'9'), others use direct numeric
        if gear_byte is not None:
            # First check for ASCII character format
            if gear_byte == ord('R') or gear_byte == ord('r'):
                gear = -1  # Reverse
            elif gear_byte == ord('N') or gear_byte == ord('n'):
                gear = 0  # Neutral
            elif ord('0') <= gear_byte <= ord('9'):
                gear = gear_byte - ord('0')
            # Then check for direct numeric format (BeamNG style - 1-indexed)
            elif 1 <= gear_byte <= 10:
                # BeamNG sends: 1=neutral, 2=gear1, 3=gear2, ..., 10=gear9
                # Convert to: 0=neutral, 1=gear1, 2=gear2, ..., 9=gear9
                gear = gear_byte - 1
            elif gear_byte == 0:
                # 0 might indicate reverse in BeamNG
                gear = -1
            elif gear_byte == 255 or gear_byte == 0xFF:
                # 0xFF might indicate reverse in some implementations
                gear = -1
            else:
                # Unknown gear value - log for debugging (only first few times to avoid spam)
                if not hasattr(parse_outgauge_packet, '_gear_warn_count'):
                    parse_outgauge_packet._gear_warn_count = 0
                if parse_outgauge_packet._gear_warn_count < 5:
                    logger.warning(f"Unknown gear byte value: {gear_byte} (0x{gear_byte:02x}, char: {chr(gear_byte) if 32 <= gear_byte < 127 else 'N/A'})")
                    parse_outgauge_packet._gear_warn_count += 1
                gear = None
        
        # Convert RPM float to int
        rpm = int(rpm_float) if rpm_float is not None else None
        
        # For MVP: G-forces are not directly in OutGauge protocol
        # We'll set them to None for now, or could calculate from speed changes
        # In a full implementation, we'd need OutSim or calculate from acceleration
        g_force_x = None
        g_force_y = None
        
        return TelemetrySample(
            speed=speed,
            rpm=rpm,
            gear=gear,
            g_force_x=g_force_x,
            g_force_y=g_force_y,
            timestamp=datetime.now(timezone.utc),
            raw_bytes=data if len(data) <= 200 else None  # Store raw bytes for debugging (limit size)
        )
        
    except struct.error as e:
        logger.warning(f"Failed to parse OutGauge packet (struct error): {e}, packet size: {len(data)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing OutGauge packet: {e}", exc_info=True)
        return None

