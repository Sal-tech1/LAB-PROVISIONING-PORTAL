# Lab Provisioning Portal — Backend

FastAPI backend that provisions isolated Docker lab containers on demand. A client selects a lab template, the API starts a container with CPU and memory limits, assigns a host port, and returns an access URL. When the session ends, the API stops and removes the container.

## What it does today

| Area | Status |
| --- | --- |
| Health check | `GET /health` — API and PostgreSQL connectivity |
| Lab session provisioning | `POST /sessions` — spawn a container from a template |
| Lab session teardown | `DELETE /sessions/{session_id}` — stop container and remove record |
| Lab templates | Seeded via `python -m backend.seed` (not exposed as API yet) |
| User accounts | `User` model exists in the database; no auth endpoints yet |

### Session lifecycle

1. Client sends `template_id` and `user_id` to `POST /sessions`.
2. Backend loads the matching `LabTemplate` (Docker image, CPU limit, RAM limit).
3. Backend finds a free host port in the range 10000–20000.
4. Backend starts a detached Docker container on the `lab-network` bridge network.
5. Backend saves an `ActiveSession` row and returns metadata including `access_url`.
6. Client calls `DELETE /sessions/{session_id}` to stop the container and delete the session.

### Seeded lab templates

Running the seed script creates two templates if the table is empty:

| Name | Image | CPU | RAM |
| --- | --- | --- | --- |
| Python Sandbox | `python:3.11-slim` | 0.5 | 512m |
| Node.js Workshop | `node:20-alpine` | 1.0 | 1g |

## Tech stack

- **FastAPI** — REST API
- **SQLAlchemy** — ORM and PostgreSQL access
- **Docker SDK** — container spawn/kill
- **Uvicorn** — ASGI server

## API reference

Base URL: `http://127.0.0.1:8000`

Interactive docs: `/docs` (Swagger) · `/redoc` (ReDoc)

### `GET /health`

Returns API status and database connectivity.

```json
{
  "status": "ok",
  "db": "connected"
}
```

### `POST /sessions`

Create a lab session and start a container.

**Request body:**

```json
{
  "template_id": 1,
  "user_id": 1
}
```

**Response:**

```json
{
  "id": 1,
  "user_id": 1,
  "template_id": 1,
  "container_id": "abc123...",
  "port": 10042,
  "status": "running",
  "access_url": "http://localhost:10042"
}
```

### `DELETE /sessions/{session_id}`

Stop the container and remove the session record.

**Response:**

```json
{
  "message": "Session deleted successfully"
}
```

## Data model

```
User ──< ActiveSession >── LabTemplate
```

| Table | Purpose |
| --- | --- |
| `users` | Portal users (email, password hash, role) — schema only for now |
| `lab_templates` | Reusable lab definitions (name, Docker image, resource limits) |
| `active_sessions` | Running sessions (container ID, assigned port, status) |

## Project layout

```
backend/
├── main.py              # FastAPI app, health check, router registration
├── database.py          # Engine, session factory, DATABASE_URL loading
├── seed.py              # Create tables and seed lab templates
├── api/
│   ├── sessions.py      # POST /sessions, DELETE /sessions/{id}
│   └── docker_utils.py  # Port allocation, container spawn/kill
├── models/
│   └── models.py        # User, LabTemplate, ActiveSession
└── tests/
    └── test_sessions.py # Session endpoint tests (mocked Docker)
```

## Prerequisites

- Python 3.11+
- PostgreSQL
- Docker Desktop (Windows/macOS) or Docker Engine (Linux) — required for session provisioning

## Setup

### 1. Install dependencies

From the project root:

```bash
python -m pip install -r backend/requirements.txt
```

### 2. Configure environment

Create `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/lab_portal
```

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection URL for SQLAlchemy |

If `DATABASE_URL` is missing, startup fails with a clear error.

### 3. Prepare Docker

Docker must be running before creating sessions.

Create the network used by provisioned containers (once):

```bash
docker network create lab-network
```

Optionally, from the **project root**, start the monitoring stack and sample lab defined in `docker-compose.yml`:

```bash
docker build -t lab-alpine:v2 docker/lab-alpine
docker compose up -d
```

| Service | URL |
| --- | --- |
| Sample lab | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (`admin` / `labportal123`) |
| Node Exporter | http://localhost:9100/metrics |

### 4. Seed the database

Creates tables and inserts lab templates:

```bash
python -m backend.seed
```

### 5. Start the server

```bash
python -m uvicorn backend.main:app --reload
```

API: http://127.0.0.1:8000

## Docker integration

Session provisioning is handled in `backend/api/docker_utils.py`:

- **`get_free_port()`** — scans ports 10000–20000 for an available host port
- **`spawn_container()`** — runs a detached container with CPU/RAM limits on `lab-network`, maps container port 80 to the assigned host port
- **`kill_container()`** — stops and force-removes a container by ID

The backend talks to the local Docker daemon via the `docker` Python package (`docker.from_env()`).

## Running tests

```bash
python -m pytest backend/tests/
```

Tests mock Docker calls so no running daemon is required.

## Common issues

### `pip` or `uvicorn` is not recognized

Use the module form:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

### PostgreSQL password authentication failed

Check the username and password in `backend/.env` match your PostgreSQL instance.

### Docker is not running

Start Docker Desktop or the Docker service before calling `POST /sessions`.

### `network lab-network not found`

```bash
docker network create lab-network
```

### Permission denied connecting to Docker (Linux)

```bash
sudo usermod -aG docker $USER
```

Log out and back in for the group change to take effect.
