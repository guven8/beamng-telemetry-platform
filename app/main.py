"""
BeamNG Telemetry Platform - Main FastAPI Application

Modular monolith architecture with feature modules:
- auth: Authentication and JWT management
- telemetry: UDP ingestion and parsing
- stream: WebSocket broadcasting
- analytics: Persistence and analytics
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.telemetry.listener import udp_listener

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown tasks.
    
    On startup:
    - Creates the telemetry queue
    - Starts the UDP listener as a background task
    
    On shutdown:
    - Cancels the UDP listener task cleanly
    """
    # Startup
    logger.info("Starting BeamNG Telemetry Platform...")
    
    # Create telemetry queue for internal communication
    app.state.telemetry_queue = asyncio.Queue()
    logger.info("Created telemetry queue")
    
    # Start UDP listener as background task
    udp_task = asyncio.create_task(udp_listener(app.state.telemetry_queue))
    logger.info("Started UDP listener background task")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BeamNG Telemetry Platform...")
    
    # Cancel UDP listener task
    if not udp_task.done():
        udp_task.cancel()
        try:
            await udp_task
        except asyncio.CancelledError:
            logger.info("UDP listener task cancelled")
    
    logger.info("Shutdown complete")


app = FastAPI(
    title="BeamNG Telemetry Platform",
    description="Real-time telemetry dashboard for BeamNG.drive",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for development
# In production, configure allowed origins appropriately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include feature module routers
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment verification."""
    return {"status": "healthy", "service": "beamng-telemetry-platform"}


@app.get("/telemetry/debug")
async def telemetry_debug():
    """
    Debug endpoint to check telemetry module status.
    
    Returns basic information about the telemetry ingestion system.
    """
    queue_size = app.state.telemetry_queue.qsize() if hasattr(app.state, 'telemetry_queue') else 0
    return {
        "status": "telemetry module active",
        "queue_size": queue_size,
        "udp_port": int(os.getenv("UDP_PORT", 4444))
    }

