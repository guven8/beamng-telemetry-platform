"""
Unit tests for telemetry parser.

Tests the parse_outgauge_packet function to ensure it correctly:
- Parses valid OutGauge packets
- Ignores MotionSim packets
- Ignores wrong-size packets
"""
import struct
from datetime import datetime
from app.modules.telemetry.parser import parse_outgauge_packet, OUTGAUGE_PACKET_SIZE, OUTGAUGE_STRUCT_FORMAT
from app.modules.telemetry.schemas import TelemetrySample


def test_parse_valid_outgauge_packet():
    """Test parsing a valid OutGauge packet."""
    # Build a synthetic 96-byte OutGauge packet
    # Format: Time(4) + Car(4) + Flags(2) + Gear(1) + PLID(1) + Speed(4) + RPM(4) + 
    #         Turbo(4) + EngTemp(4) + Fuel(4) + OilPressure(4) + OilTemp(4) +
    #         DashLights(4) + ShowLights(4) + Throttle(4) + Brake(4) + Clutch(4) +
    #         Display1(12) + Display2(12) + ID(4)
    
    time = 12345
    car = b"beam"
    flags = 0
    gear = b'3'  # Gear 3 (ASCII '3') - must be bytes for 'c' format
    plid = 0
    speed = 25.5  # m/s
    rpm = 3500.0
    turbo = 0.0
    eng_temp = 90.0
    fuel = 0.75
    oil_pressure = 50.0
    oil_temp = 85.0
    dash_lights = 0
    show_lights = 0
    throttle = 0.8
    brake = 0.0
    clutch = 0.0
    display1 = b"SPEED      \x00"  # Must be exactly 12 bytes (pad with null)
    display2 = b"RPM        \x00"  # Must be exactly 12 bytes (pad with null)
    packet_id = 1
    
    # Pack the data according to OUTGAUGE_STRUCT_FORMAT
    # Format: <I4sHcBffffffffIIffff12s12si (22 items total)
    # Structure: I(1) + 4s(1) + H(1) + c(1) + B(1) + ffffffff(8) + II(2) + ffff(4) + 12s(1) + 12s(1) + i(1)
    # The 8 floats (ffffffff): speed, rpm, turbo, eng_temp, fuel, oil_pressure, oil_temp, unused_float
    # The 4 floats after II (ffff): throttle, brake, clutch, unused_float
    packet = struct.pack(
        OUTGAUGE_STRUCT_FORMAT,
        time,           # I
        car,            # 4s
        flags,          # H
        gear,           # c
        plid,           # B
        speed,          # f (1/8)
        rpm,            # f (2/8)
        turbo,          # f (3/8)
        eng_temp,       # f (4/8)
        fuel,           # f (5/8)
        oil_pressure,   # f (6/8)
        oil_temp,       # f (7/8)
        0.0,            # f (8/8) - unused float
        dash_lights,    # I
        show_lights,    # I
        throttle,       # f (1/4)
        brake,          # f (2/4)
        clutch,         # f (3/4)
        0.0,            # f (4/4) - unused float
        display1,       # 12s
        display2,       # 12s
        packet_id       # i
    )
    
    # Parse the packet
    result = parse_outgauge_packet(packet)
    
    # Assertions
    assert result is not None, "Should return a TelemetrySample"
    assert isinstance(result, TelemetrySample), "Should return TelemetrySample instance"
    assert result.speed == speed, f"Speed should be {speed} m/s, got {result.speed}"
    assert result.rpm == int(rpm), f"RPM should be {int(rpm)}, got {result.rpm}"
    assert result.gear == 3, f"Gear should be 3, got {result.gear}"
    assert isinstance(result.timestamp, datetime), "Timestamp should be a datetime object"


def test_parse_outgauge_packet_with_reverse_gear():
    """Test parsing OutGauge packet with reverse gear."""
    time = 0
    car = b"test"
    flags = 0
    gear = b'R'  # Reverse gear - must be bytes for 'c' format
    plid = 0
    speed = 5.0
    rpm = 1000.0
    turbo = 0.0
    eng_temp = 80.0
    fuel = 0.5
    oil_pressure = 40.0
    oil_temp = 75.0
    dash_lights = 0
    show_lights = 0
    throttle = 0.3
    brake = 0.0
    clutch = 0.0
    display1 = b"            \x00"  # 12 bytes
    display2 = b"            \x00"  # 12 bytes
    packet_id = 0
    
    packet = struct.pack(
        OUTGAUGE_STRUCT_FORMAT,
        time, car, flags, gear, plid, speed, rpm,
        turbo, eng_temp, fuel, oil_pressure, oil_temp,
        0.0,  # Unused float field
        dash_lights, show_lights, throttle, brake, clutch,
        0.0,  # Unused float field
        display1, display2, packet_id
    )
    
    result = parse_outgauge_packet(packet)
    
    assert result is not None
    assert result.gear == -1, f"Reverse gear should be -1, got {result.gear}"


def test_parse_outgauge_packet_with_neutral_gear():
    """Test parsing OutGauge packet with neutral gear."""
    time = 0
    car = b"test"
    flags = 0
    gear = b'N'  # Neutral gear - must be bytes for 'c' format
    plid = 0
    speed = 0.0
    rpm = 800.0
    turbo = 0.0
    eng_temp = 70.0
    fuel = 0.5
    oil_pressure = 30.0
    oil_temp = 70.0
    dash_lights = 0
    show_lights = 0
    throttle = 0.0
    brake = 0.0
    clutch = 0.0
    display1 = b"            \x00"  # 12 bytes
    display2 = b"            \x00"  # 12 bytes
    packet_id = 0
    
    packet = struct.pack(
        OUTGAUGE_STRUCT_FORMAT,
        time, car, flags, gear, plid, speed, rpm,
        turbo, eng_temp, fuel, oil_pressure, oil_temp,
        0.0,  # Unused float field
        dash_lights, show_lights, throttle, brake, clutch,
        0.0,  # Unused float field
        display1, display2, packet_id
    )
    
    result = parse_outgauge_packet(packet)
    
    assert result is not None
    assert result.gear == 0, f"Neutral gear should be 0, got {result.gear}"


def test_parse_outgauge_packet_ignores_motionsim():
    """Test that MotionSim packets (starting with BNG1) are ignored."""
    # MotionSim packet starts with "BNG1" header
    motionsim_packet = b"BNG1" + b"\x00" * 92  # 96 bytes total
    
    result = parse_outgauge_packet(motionsim_packet)
    
    assert result is None, "MotionSim packets should be ignored and return None"


def test_parse_outgauge_packet_ignores_wrong_size():
    """Test that packets with wrong size are ignored."""
    # Too short
    short_packet = b"\x00" * 50
    result = parse_outgauge_packet(short_packet)
    assert result is None, "Packets shorter than 96 bytes should be ignored"
    
    # Too long
    long_packet = b"\x00" * 120
    result = parse_outgauge_packet(long_packet)
    assert result is None, "Packets longer than 96 bytes should be ignored"
    
    # Exactly 96 bytes but invalid structure (should still try to parse)
    # This will likely fail struct parsing, but we test the size check first
    invalid_96_byte = b"\x00" * 96
    # This might return None due to struct error, which is acceptable
    result = parse_outgauge_packet(invalid_96_byte)
    # Either None (struct error) or a TelemetrySample with None values is acceptable
    # The important thing is it doesn't crash


def test_parse_outgauge_packet_with_beamng_gear_format():
    """Test parsing with BeamNG's 1-indexed gear format."""
    # BeamNG uses 1-indexed: 1=neutral, 2=gear1, 3=gear2, etc.
    time = 0
    car = b"beam"
    flags = 0
    gear = bytes([4])  # BeamNG format: 4 = gear 3 (1-indexed, so 4-1=3) - must be bytes for 'c' format
    plid = 0
    speed = 30.0
    rpm = 4000.0
    turbo = 0.0
    eng_temp = 95.0
    fuel = 0.6
    oil_pressure = 55.0
    oil_temp = 90.0
    dash_lights = 0
    show_lights = 0
    throttle = 1.0
    brake = 0.0
    clutch = 0.0
    display1 = b"            \x00"  # 12 bytes
    display2 = b"            \x00"  # 12 bytes
    packet_id = 0
    
    packet = struct.pack(
        OUTGAUGE_STRUCT_FORMAT,
        time, car, flags, gear, plid, speed, rpm,
        turbo, eng_temp, fuel, oil_pressure, oil_temp,
        0.0,  # Unused float field
        dash_lights, show_lights, throttle, brake, clutch,
        0.0,  # Unused float field
        display1, display2, packet_id
    )
    
    result = parse_outgauge_packet(packet)
    
    assert result is not None
    # BeamNG format: 4 should convert to gear 3 (4-1=3)
    assert result.gear == 3, f"BeamNG gear 4 should convert to gear 3, got {result.gear}"
