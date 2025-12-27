# BeamNG Telemetry Platform – Modular Monolith Demo

A lean, self-hosted real-time telemetry platform built for BeamNG.drive.  
This project demonstrates platform engineering skills aligned with BeamNG’s philosophy:
simple, maintainable systems, modular monolith architecture, Linux-first deployment, and AI-assisted yet human-led development.

The project ingests BeamNG telemetry via UDP, processes it, streams it in real-time to the browser, and stores structured sessions for analytics and replay.

---

## 1️⃣ Objectives

- Build a **real-time telemetry dashboard** for BeamNG.drive.
- Demonstrate:
  - Modular Monolith Architecture
  - Real-time ingestion & streaming
  - Persistence & analytics
  - Clean, maintainable FastAPI + Vue 3 codebase
  - Lightweight Docker deployment
- Be realistic: optimize for **clarity, maintainability, correctness, simplicity (KISS)**.

---

## 2️⃣ Core Principles
- **Minimal local login** for a single seeded user
- **JWT issuance**
- **JWT middleware** for protected HTTP routes and WebSocket connections
- **Modular Monolith**, not microservices.
- **KISS over Cleverness**
  - Prefer boring, understandable solutions.
- **Self-Hosted, Lightweight**
  - Docker Compose only
  - No Kubernetes
  - No cloud dependencies required.
- **Async First**
  - UDP ingestion must not block request handling.
- **Minimal Dependencies**
  - Only use what is truly necessary.
- **Readable Architecture**
  - Clear domains and module boundaries.
- **AI-Assisted Development**
  - AI helps execute → Human provides architecture, decisions, & refinements.

---

## 3️⃣ System Overview

BeamNG (UDP OutGauge)
    → FastAPI UDP Listener
    → Telemetry Parser
    → Internal asyncio Queue
        → WebSocket Broadcaster → Vue 3 Dashboard (real-time view)
        → Persistence Layer → PostgreSQL (sessions & frames) → Analytics / Session Replay

---

## 4️⃣ Tech Stack

**Backend**
- Python 3.12
- FastAPI
- Async UDP Listener
- WebSockets

**Frontend**
- Vue 3 + Composition API
- Vite
- Pinia
- TailwindCSS

**Database**
- PostgreSQL

**Infrastructure**
- Docker Compose
- Linux-first
- Nginx Reverse Proxy (optional production mode)

---

## 5️⃣ Feature Modules

### A. Identity Module (`app/modules/auth`)
- Minimal local authentication for demo purposes.
- Single seeded user in the database (e.g. `local`).
- Login endpoint that returns a JWT for that user.
- Store (minimum):
  - username
  - hashed password
  - last seen IP
  - `fumbletron_token`
- Provide middleware for protected routes.
- Provide WebSocket authentication using the JWT.
- Full registration / multi-user flows are out of scope for this MVP and can be documented as future improvements.


---

### B. Telemetry Ingestion Module (`app/modules/telemetry`)
- Async UDP listener on configurable port (default `4444`)
- Parse **OutGauge protocol compatible payload**
- Store raw → structured fields:
  - speed
  - rpm
  - gear
  - g-force-x
  - g-force-y
  - throttle/brake (if present)
- Forward parsed packets to an internal `asyncio.Queue`
- Associate telemetry with a user
  - initially map based on client IP
- MUST NOT block FastAPI worker threads

---

### C. Streaming Module (`app/modules/stream`)
- WebSocket Manager
- Broadcast telemetry in real time
- Only send data to:
  - authenticated user
  - telemetry that belongs to them

---

### D. Analytics & Persistence Module (`app/modules/analytics`)
- Store telemetry frames in PostgreSQL
- Session logic:
  - Start session when movement begins
  - End after inactivity timeout
- Analytics:
  - Top Speed
  - Max lateral G
  - Avg speed
  - Simple consistency metric

---

## 6️⃣ Database Model (High Level)

`users`
- id
- username
- password_hash
- last_ip
- fumbletron_token

`sessions`
- id
- user_id
- car_name (optional now)
- start_time
- end_time

`telemetry_frames`
- session_id
- timestamp
- speed
- rpm
- gear
- g_force_x
- g_force_y
- fuel (optional)

---

## 7️⃣ Real-Time Data Path

1️⃣ BeamNG sends UDP packets → server receives  
2️⃣ Parse packets → create structured object  
3️⃣ Push into internal queue  
4️⃣ WebSocket broadcaster consumes queue  
5️⃣ Vue dashboard updates instantly

No Redis.  
No Kafka.  
No unnecessary infra.

### Ingestion vs UI Login

- The UDP listener runs continuously and ingests telemetry regardless of who is logged into the web UI.
- Telemetry is associated with the configured user and persisted to PostgreSQL even if no browser client is connected.
- Authentication is required only to:
  - access the dashboard,
  - open a WebSocket connection,
  - view live telemetry and historical sessions.


---

## 8️⃣ Implementation Order (IMPORTANT)

The AI assistant must follow this order:

1️⃣ Project bootstrap
- FastAPI app
- Module folder structure
- Health check endpoint

2️⃣ Auth module
- Register
- Login
- JWT middleware

3️⃣ UDP ingestion
- Async listener
- Simple logging
- OutGauge parser

4️⃣ WebSocket streaming
- Authenticated WS endpoint
- Broadcast dummy data
- Then integrate real telemetry

5️⃣ Frontend MVP
- Vue 3 app
- Login page
- Dashboard page
- Display live values (numeric + charts)

6️⃣ Persistence + sessions
- Database schema
- Save frames
- Session start / stop logic

7️⃣ Analytics
- Basic calculations
- Display in UI

8️⃣ Polish
- Documentation
- Comments
- Clean structure

---

## 9️⃣ Deployment Target

Local development:
- Docker Compose
- App container
- PostgreSQL
- Optional Nginx

Production Notes:
- HTTPS via Nginx
- Systemd optional install docs

---

## 🔟 Known Limitations & Intentional Scope Constraints

- Currently assumes **single-instance deployment**
- Multi-tenant mapped via IP for MVP
- NAT / VPN edge cases acknowledged
- Future solution:
  - authenticated ingest token
  - explicit client mapping

This is acceptable and documented.

---

## 1️⃣1️⃣ Fumbletron-3156 Compliance

We store:
- `fumbletron_token`
- Validation boolean

Display badge:

**Fumbletron-3156: VALID**

This is humorous but intentional and demonstrates a small, custom validation/entitlement flag in the user system.


---

## 1️⃣2️⃣ Documentation Expectations

The codebase MUST contain:
- Clear docstrings
- Architecture explanation
- How to run locally
- How to point BeamNG to the server

---

## 1️⃣3️⃣ Success Criteria

The project is successful when:
- BeamNG sends telemetry
- Dashboard updates in real time
- Sessions appear in history
- Basic analytics work
- System remains simple & readable
