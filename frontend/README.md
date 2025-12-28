# BeamNG Telemetry Platform - Frontend

Vue 3 + Vite frontend for the BeamNG Telemetry Platform.

## Setup

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

## Configuration

The frontend connects to the backend API at `http://localhost:8000` by default.

To change the API URL, create a `.env` file:
```
VITE_API_BASE=http://localhost:8000
VITE_WS_BASE=ws://localhost:8000
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Features

- **Login Page**: Authenticate with the backend API
- **Dashboard**: Real-time telemetry display with WebSocket connection
- **Live Charts**: Speed over time visualization
- **Metric Cards**: Display speed, RPM, gear, and G-forces


