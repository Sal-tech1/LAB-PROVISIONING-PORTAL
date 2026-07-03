# Project Setup

## 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 2. Configure environment variables

Create a `.env` file in the `backend/` directory with your PostgreSQL connection string:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/lab_portal
```

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy connection URL for PostgreSQL. Replace `postgres`, `password`, `localhost`, `5432`, and `lab_portal` with your username, password, host, port, and database name. |

The app loads this file from `backend/.env` when you run the seed script or start the server. If `DATABASE_URL` is missing, startup fails with a clear error.

## 3. Seed the database

This creates the required database tables and inserts the initial data.

```bash
python -m backend.seed
```

If successful, you should see something similar to:

```text
Skipping seed: 2 lab template(s) already exist.
```

## 4. Start the development server

Run the FastAPI server with auto-reload enabled:

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

* http://127.0.0.1:8000

Interactive API documentation:

* Swagger UI: http://127.0.0.1:8000/docs
* ReDoc: http://127.0.0.1:8000/redoc

## Common Issues

### `pip` is not recognized

Use:

```bash
python -m pip install -r requirements.txt
```

instead of:

```bash
pip install -r requirements.txt
```

### `uvicorn` is not recognized

Use:

```bash
python -m uvicorn backend.main:app --reload
```

instead of:

```bash
uvicorn backend.main:app --reload
```

### PostgreSQL password authentication failed

Ensure your database configuration uses the correct PostgreSQL username (commonly `postgres`) and the correct password in your `.env` file or database configuration.
