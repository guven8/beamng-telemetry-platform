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
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.modules.auth.router import router as auth_router
from app.modules.telemetry.listener import udp_listener
from app.modules.stream.router import router as stream_router
from app.modules.stream.consumer import telemetry_consumer
from app.modules.analytics.router import router as analytics_router
from app.modules.analytics.persistence import persistence_worker
from app.modules.analytics.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown tasks.
    
    On startup:
    - Creates the telemetry queue
    - Starts the UDP listener as a background task
    - Starts the telemetry consumer as a background task
    
    On shutdown:
    - Cancels all background tasks cleanly
    """
    # Startup
    logger.info("Starting BeamNG Telemetry Platform...")
    
    # Initialize database tables
    # Note: Models are imported inside init_db() to ensure they're registered
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        logger.error("Continuing without database - persistence will not work")
    
    # Create telemetry queue for internal communication
    app.state.telemetry_queue = asyncio.Queue()
    logger.info("Created telemetry queue")
    
    # Start UDP listener as background task
    udp_task = asyncio.create_task(udp_listener(app.state.telemetry_queue))
    logger.info("Started UDP listener background task")
    
    # Start telemetry consumer as background task
    consumer_task = asyncio.create_task(telemetry_consumer(app.state.telemetry_queue))
    logger.info("Started telemetry consumer background task")
    
    # Start persistence worker as background task
    persistence_task = asyncio.create_task(persistence_worker(app.state.telemetry_queue))
    logger.info("Started persistence worker background task")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BeamNG Telemetry Platform...")
    
    # Cancel persistence worker task
    if not persistence_task.done():
        persistence_task.cancel()
        try:
            await persistence_task
        except asyncio.CancelledError:
            logger.info("Persistence worker task cancelled")
    
    # Cancel telemetry consumer task
    if not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Telemetry consumer task cancelled")
    
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

# Include feature module routers (must be before static file serving)
app.include_router(auth_router)
app.include_router(stream_router)
app.include_router(analytics_router)


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

# Serve static frontend files (built Vue app)
# Check if static directory exists (Docker build) or use frontend/dist (local dev)
static_path = Path("/app/static")
if not static_path.exists():
    static_path = Path(__file__).parent.parent / "frontend" / "dist"

if static_path.exists():
    # Mount static assets (JS, CSS, images, etc.)
    assets_dir = static_path / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Serve index.html for root and all non-API routes (SPA routing)
    # This must be last so API routes take precedence
    @app.get("/")
    async def serve_index():
        """Serve frontend index.html for root path."""
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"detail": "Frontend not found"}
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """
        Serve frontend index.html for all non-API routes (SPA routing).
        API routes are handled by routers above, so they take precedence.
        """
        # Skip if this is an API route (shouldn't happen due to route order, but safety check)
        if full_path.startswith(("auth/", "sessions", "ws/", "health", "telemetry/")):
            return {"detail": "Not found"}
        
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"detail": "Frontend not found"}

