"""
BeamNG Telemetry Platform - Main FastAPI Application

Modular monolith architecture with feature modules:
- auth: Authentication and JWT management
- telemetry: UDP ingestion and parsing
- stream: WebSocket broadcasting
- analytics: Persistence and analytics
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BeamNG Telemetry Platform",
    description="Real-time telemetry dashboard for BeamNG.drive",
    version="0.1.0"
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


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment verification."""
    return {"status": "healthy", "service": "beamng-telemetry-platform"}

