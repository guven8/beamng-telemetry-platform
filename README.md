# BeamNG Telemetry Platform

A lean, self-hosted real-time telemetry platform built for BeamNG.drive.

## Features

- Real-time telemetry ingestion via UDP (OutGauge protocol)
- WebSocket streaming to web dashboard
- Session management with automatic start/stop
- PostgreSQL persistence
- Vue 3 frontend with live charts

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- Docker and Docker Compose (for PostgreSQL)

### Backend Setup

1. Start PostgreSQL:
```bash
docker-compose up -d postgres
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Configure BeamNG.drive

1. Open BeamNG.drive settings
2. Go to Controls → Advanced → OutGauge
3. Enable OutGauge
4. Set IP to your server's IP (or `127.0.0.1` for local)
5. Set port to `4444` (or set `UDP_PORT` environment variable)

## API Endpoints

- `POST /auth/login` - Login and get JWT token
- `GET /health` - Health check
- `GET /telemetry/debug` - Telemetry debug info
- `WS /ws/telemetry?token=<jwt>` - WebSocket for real-time telemetry
- `GET /sessions` - List all sessions (requires auth)
- `GET /sessions/{id}` - Get session detail with frames (requires auth)

## Environment Variables

- `UDP_PORT` - UDP port for telemetry (default: 4444)
- `JWT_SECRET_KEY` - Secret key for JWT (default: dev key)
- `SEEDED_USER_PASSWORD` - Password for seeded user (default: "local")
- `DATABASE_URL` - PostgreSQL connection string (default: postgresql://beamng:beamng@localhost:5432/beamng_telemetry)

## Architecture

- **Modular Monolith** - Feature modules: auth, telemetry, stream, analytics
- **Async First** - Non-blocking UDP ingestion and WebSocket streaming
- **Simple & Maintainable** - KISS principle, minimal dependencies

## License

See LICENSE file.
