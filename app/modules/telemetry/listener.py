"""
Async UDP listener for receiving BeamNG.drive telemetry packets.

Runs as a background task, receives UDP packets, parses them, and queues
TelemetrySample objects for consumption by the streaming and persistence modules.
"""
import asyncio
import logging
import os
from app.modules.telemetry.parser import parse_outgauge_packet

logger = logging.getLogger(__name__)

# Default UDP port for OutGauge (BeamNG standard)
DEFAULT_UDP_PORT = 4444


async def udp_listener(queue: asyncio.Queue) -> None:
    """
    Async UDP listener that receives OutGauge packets and queues parsed telemetry.
    
    Reads UDP_PORT from environment (defaults to 4444).
    Binds to 0.0.0.0 to accept connections from any interface.
    Parses each packet and puts TelemetrySample into the queue if valid.
    
    This runs in a background task and does not block FastAPI request handling.
    
    Args:
        queue: asyncio.Queue to put parsed TelemetrySample objects into
    """
    # Get UDP port from environment
    udp_port = int(os.getenv("UDP_PORT", DEFAULT_UDP_PORT))
    
    logger.info(f"Starting UDP listener on 0.0.0.0:{udp_port}")
    
    # Create UDP socket
    loop = asyncio.get_event_loop()
    transport = None
    
    try:
        # Create UDP endpoint
        sock = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(queue),
            local_addr=('0.0.0.0', udp_port)
        )
        transport, protocol = sock
        
        logger.info(f"UDP listener bound to 0.0.0.0:{udp_port}, waiting for packets...")
        
        # Keep running until cancelled
        while True:
            await asyncio.sleep(1)  # Prevent busy-waiting
            
    except asyncio.CancelledError:
        logger.info("UDP listener cancelled, shutting down...")
        raise
    except Exception as e:
        logger.error(f"UDP listener error: {e}", exc_info=True)
        raise
    finally:
        if transport:
            transport.close()
        logger.info("UDP listener closed")


class UDPProtocol(asyncio.DatagramProtocol):
    """
    Datagram protocol handler for UDP packets.
    
    Receives UDP datagrams and processes them asynchronously.
    """
    
    def __init__(self, queue: asyncio.Queue):
        """Initialize with the telemetry queue."""
        self.queue = queue
        self.packet_count = 0
        self.error_count = 0
    
    def datagram_received(self, data: bytes, addr: tuple) -> None:
        """
        Called when a UDP datagram is received.
        
        Args:
            data: Raw packet bytes
            addr: Tuple of (host, port) of sender
        """
        self.packet_count += 1
        
        # Parse the packet
        sample = parse_outgauge_packet(data)
        
        if sample is None:
            self.error_count += 1
            if self.error_count % 100 == 0:  # Log every 100th error to avoid spam
                logger.warning(f"Failed to parse packet from {addr} (total errors: {self.error_count})")
            return
        
        # Log basic info periodically (every 100 packets to avoid spam)
        if self.packet_count % 100 == 0:
            logger.info(
                f"Packet #{self.packet_count} from {addr}: "
                f"speed={sample.speed:.1f}m/s, rpm={sample.rpm}, gear={sample.gear}"
            )
        
        # Put sample into queue (non-blocking)
        try:
            self.queue.put_nowait(sample)
        except asyncio.QueueFull:
            logger.warning("Telemetry queue is full, dropping packet")
    
    def error_received(self, exc: Exception) -> None:
        """Called when a receive error occurs."""
        logger.error(f"UDP receive error: {exc}")

