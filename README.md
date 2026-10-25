# Customers API

REST API to manage the customers of a financial platform, built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2** and **Alembic**, and packaged with **Docker**.

## Stack

| Area                | Technology                 |
|---------------------|----------------------------|
| Framework           | FastAPI + Pydantic v2      |
| Database            | PostgreSQL 17              |
| ORM / Migrations    | SQLAlchemy 2 + Alembic     |
| Testing             | Pytest + TestClient        |
| Code quality        | Ruff (lint + format)       |
| Infrastructure      | Docker / Docker Compose    |

## Quick start (Docker)

Requirements: Docker with Compose (or Podman with `podman-compose`).

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

On startup the API container applies the database migrations automatically (`alembic upgrade head`).

Sample data (25 customers with mixed statuses; idempotent, safe to run several times):

```bash
docker compose exec api python -m scripts.seed
```

The script goes through the use cases, so the same business rules as the API apply.

## Local development (API outside Docker)

Requirements: Python 3.14+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

docker compose up -d db        # database only
alembic upgrade head           # create the schema
uvicorn app.main:app --reload
```

## Tests

```bash
pytest                                     # in-memory SQLite (fast, no dependencies)

# The same suite against a real PostgreSQL:
docker compose exec db psql -U customers -c "CREATE DATABASE customers_test;"
TEST_DATABASE_URL=postgresql+psycopg://customers:customers@localhost:5432/customers_test pytest
```

The suite includes:

- **Integration tests** (`tests/test_customers_api.py`, `tests/test_health.py`): exercise every layer over HTTP.
- **Unit tests** (`tests/test_use_cases.py`, `tests/test_utils.py`): each use case and the domain validator against an in-memory repository.
- **Cross-cutting tests** (`tests/test_cross_cutting.py`): error envelope, `500` without leaking details, `X-Request-ID`, logs without personal data and CORS.

Lint and format:

```bash
ruff check . && ruff format --check .
```

## Endpoints

| Method  | Path                                       | Description                                          | Responses     |
|---------|--------------------------------------------|------------------------------------------------------|---------------|
| `POST`  | `/customers`                               | Create a customer (`status = PENDING`)               | 201, 409, 422 |
| `GET`   | `/customers?status=&search=&page=&size=`   | Paginated list with optional status filter and search | 200, 422     |
| `GET`   | `/customers/summary?days=`                 | Totals per status and daily registrations            | 200, 422      |
| `GET`   | `/customers/{customer_id}`                 | Get a customer                                       | 200, 404, 422 |
| `PATCH` | `/customers/{customer_id}/status`          | Update the status                                    | 200, 404, 422 |
| `GET`   | `/health`                                  | Health check                                         | 200           |

Allowed statuses: `ACTIVE`, `PENDING`, `BLOCKED`.
Pagination: `page` ≥ 1 (default `1`), `size` between 1 and 100 (default `20`).
Search: `search` matches name or email partially, case-insensitive.

### Response format

Every `/customers` response shares the same envelope, so clients always know where to find the data or the error:

```jsonc
// Single resource
{ "success": true, "data": { ... } }

// Paginated collection
{ "success": true, "data": [ ... ], "meta": { "page": 1, "size": 20, "total": 42, "pages": 3 } }

// Error
{ "success": false, "error": { "code": "CUSTOMER_NOT_FOUND", "message": "...", "details": null } }
```

| `error.code`                         | HTTP | When                                                              |
|--------------------------------------|------|-------------------------------------------------------------------|
| `VALIDATION_ERROR`                   | 422  | Invalid data; `details` lists `{ field, message }` per field.     |
| `CUSTOMER_NOT_FOUND`                 | 404  | The customer does not exist.                                      |
| `EMAIL_ALREADY_EXISTS`               | 409  | The email is already registered.                                  |
| `NOT_FOUND`, `METHOD_NOT_ALLOWED`, … | 4xx  | Unknown route, method not allowed, etc.                           |
| `INTERNAL_ERROR`                     | 500  | Unexpected error (internal details are never exposed).            |

`GET /health` returns exactly `{"status": "ok"}` (no envelope), as the assignment requires and orchestrators expect.

### Usage examples

```bash
# Create a customer
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"name": "Juan Pérez", "email": "juan@example.com"}'
```

```json
{
  "success": true,
  "data": {
    "id": "3024a60e-c2c1-4cea-a189-955366d55088",
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "status": "PENDING",
    "created_at": "2026-10-25T05:09:26.640552Z"
  }
}
```

```bash
# List (paginated) / filter by status / search
curl "http://localhost:8000/customers?page=1&size=10"
curl "http://localhost:8000/customers?status=ACTIVE"
curl "http://localhost:8000/customers?search=juan&status=PENDING"

# Summary for the dashboard
curl http://localhost:8000/customers/summary

# Get a customer
curl http://localhost:8000/customers/3024a60e-c2c1-4cea-a189-955366d55088

# Update the status
curl -X PATCH http://localhost:8000/customers/3024a60e-c2c1-4cea-a189-955366d55088/status \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE"}'

# Health check
curl http://localhost:8000/health
```

Errors:

```jsonc
// 409 Conflict
{ "success": false, "error": { "code": "EMAIL_ALREADY_EXISTS", "message": "A customer with email 'juan@example.com' already exists", "details": null } }

// 422 Unprocessable Content
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      { "field": "name", "message": "String should have at least 1 character" },
      { "field": "email", "message": "value is not a valid email address: An email address must have an @-sign." }
    ]
  }
}
```

## Logging and traceability

Every request gets a **request id** (the `X-Request-ID` header is reused when the client sends a valid one; otherwise one is generated). It is returned in the response and added to **every** log line of that request, including the ones written by inner layers:

```
2026-10-25 05:18:09,316 WARNING  [demo-123] app.shared.error_handler - Business rule violated: EMAIL_ALREADY_EXISTS on POST /customers
2026-10-25 05:18:09,316 INFO     [demo-123] app.request - POST /customers -> 409 (7.4 ms)
```

- `INFO`: every request (method, path, status, duration) and business events (customer created, status changed).
- `WARNING`: business rule violations.
- `ERROR`: unexpected errors, with the full stack trace (the client only receives `INTERNAL_ERROR`).
- No personal data (name, email) is logged, only identifiers.
- Level configurable through `LOG_LEVEL`.

## Database connection

The `Database` class (`app/infrastructure/database/database.py`) is a lazy, thread-safe **singleton** (double-checked locking):

- There is **a single `Engine` per process**, and therefore a single connection pool (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `pool_pre_ping` to discard dead connections).
- It is created by the first request that needs it, not at import time, so tests and Alembic never open unnecessary connections.
- **Each request gets its own `Session`** (unit of work), closed at the end of the request, which returns the connection to the pool. The session is deliberately not a singleton: sharing it across concurrent requests is unsafe.
- The pool is released cleanly when the application shuts down (`lifespan`, inside a `try/finally`).

## Architecture

**Clean Architecture** with four layers, the same structure as the team's other services (`domain` / `application` / `infrastructure` / `shared`), plus `presentation` for the FastAPI HTTP layer. Dependencies always point towards the domain:

```
presentation ──► application ──► domain ◄── infrastructure
 (FastAPI)        (use cases)    (rules)     (SQLAlchemy, PostgreSQL)
```

```
HTTP ──► router ──► UseCase.execute() ──► CustomerRepository (port, domain)
           │                                      ▲
      Request DTO                                 │ implements
           │                         SqlAlchemyCustomerRepository ──► PostgreSQL
      Response DTO ◄── ResponseMapper ◄── Entity ◄── ModelMapper ◄── Model (ORM)
```

```
app/
├── main.py                          # App factory: logging, middleware, routers, handlers and lifespan
├── config/
│   └── settings.py                  # Settings (environment variables), read by the whole app
├── domain/                          # Business rules. Pure Python: no FastAPI, SQLAlchemy or Pydantic
│   ├── entities/                    # Customer, CustomerStatus, CustomerFilters, CustomerSummary
│   ├── errors/                      # DomainError and business errors (with code and HTTP status)
│   ├── repositories/                # Port: CustomerRepository (abstract contract)
│   └── validators/                  # Customer invariants, enforced for every entry point
├── application/
│   └── use_cases/                   # One class per operation, with execute()
│       ├── create_customer.py
│       ├── list_customers.py
│       ├── get_customer.py
│       ├── update_customer_status.py
│       └── get_customers_summary.py
├── infrastructure/                  # Replaceable technical details
│   ├── database/
│   │   ├── database.py              # Engine singleton + one Session per request
│   │   └── models/                  # ORM models (`customers` table)
│   ├── mappers/                     # Model ⇄ Entity
│   └── repositories/                # Adapter: SqlAlchemyCustomerRepository
├── presentation/                    # HTTP layer
│   ├── routers/                     # Endpoints (customers, health)
│   ├── dtos/                        # requests.py (what may be sent) · responses.py (what is exposed)
│   ├── mappers/                     # Entity → Response DTO
│   ├── middleware.py                # X-Request-ID, per-request log line, controlled 500
│   └── dependencies.py              # Composition root: wires use cases to the adapter
└── shared/
    ├── api_response.py              # Standard envelope: SuccessResponse, PaginatedResponse, ErrorResponse
    ├── error_handler.py             # DomainError / validation / HTTP errors → error envelope
    ├── logging.py                   # Log configuration and request id (used by every layer)
    ├── pagination.py                # PageRequest, Page
    └── utils/                       # Dependency-free helpers (as_utc)
alembic/                             # Database migrations
scripts/                             # Sample data seed (goes through the use cases)
specs/                               # Functional specification (SDD)
tests/                               # Unit (use cases), integration (HTTP) and cross-cutting tests
```

Dependency rules (verifiable with `grep`):

- `domain/` imports no other layer and no FastAPI, SQLAlchemy or Pydantic.
- `application/` only depends on `domain/` (and `shared/`).
- `infrastructure/` implements the domain ports and never imports `application/` or `presentation/`.
- `presentation/dependencies.py` is the only place that decides which adapter implements each port.

| Layer / piece              | Responsibility                                                                           |
|----------------------------|------------------------------------------------------------------------------------------|
| **Entity**                 | The customer in the domain; encapsulates rules such as "starts as `PENDING`".            |
| **Validator**              | Business invariants (name required, valid email) for every entry point.                  |
| **Repository (port)**      | Persistence contract used by the use cases.                                              |
| **Use case**               | One business operation (create, list, get, change status, summary).                      |
| **Model + ModelMapper**    | ORM table and its translation to/from the entity.                                        |
| **Repository (adapter)**   | SQLAlchemy implementation; turns `IntegrityError` into `EmailAlreadyExistsError`.        |
| **Router**                 | Receives the request, runs the use case and maps the entity to the response DTO.         |
| **Request / Response DTO** | What may be sent (`extra="forbid"`) and what is exposed; the entity is never serialized. |

## Technical decisions

- **Spec-Driven Development**: the behaviour is defined in [`specs/customers.spec.md`](specs/customers.spec.md) as acceptance criteria (`AC-01` … `AC-27`). Every test references the criterion it verifies.
- **Clean Architecture, like the rest of the team's services**: same layers (`domain`, `application`, `infrastructure`, `shared`) so any developer finds their way around every repo the same way. `presentation/` is added because FastAPI has routers, DTOs and middleware that are not data infrastructure.
- **One use case per operation** (`CreateCustomerUseCase.execute()`…): each operation is read, tested and changed in isolation, instead of a service that grows without limit.
- **Two-level validation**: DTOs validate the shape of the HTTP request (immediate 422) and `domain/validators` guarantees the business invariants for any entry point (for example, the seed script).
- **Entity separate from the ORM model**: business logic does not depend on SQLAlchemy, so use cases are tested with an in-memory repository and persistence can change without touching the domain.
- **Explicit request and response DTOs**: requests accept only the allowed fields (`extra="forbid"`) and responses are built field by field in the mapper. If the entity gains internal fields, they never leak into the API unless deliberately added to the response.
- **Domain errors → HTTP in a single place**: each domain error declares its stable `code` (`CUSTOMER_NOT_FOUND`, `EMAIL_ALREADY_EXISTS`) and its status, and `shared/error_handler.py` turns them into the error envelope without knowing the concrete types. Use cases know nothing about HTTP.
- **Uniform response envelope** (`success` / `data` / `meta` / `error`) with machine-readable error codes, so the frontend never has to parse messages.
- **`page`/`size` pagination** with a stable order (`created_at DESC, id DESC`), so a record never shows up on two pages.
- **Unique email, doubly protected**: the use case checks before inserting and there is also a `UNIQUE` index in the database; if two concurrent requests pass the check, the repository turns the `IntegrityError` into a `409`.
- **Emails normalized to lowercase**: `Juan@Example.com` and `juan@example.com` are the same customer.
- **UUID identifiers**: avoids exposing sequential, enumerable IDs, which is desirable on a financial platform.
- **`created_at` in UTC with timezone**, generated by the domain.
- **Status stored as `VARCHAR` + `CHECK`** (instead of a native PostgreSQL `ENUM`): adding statuses later is a trivial migration and the schema also works on SQLite for the tests.
- **Automatic migrations on container startup** through `docker-entrypoint.sh`.
- **Unprivileged container**: the API runs as a non-root user.
- **CORS** only open to `localhost` / `127.0.0.1` on any port for development (Vite switches port when 5173 is busy). In production the regex is disabled and the real domains are listed in `CORS_ORIGINS`.

## Environment variables

| Variable            | Description                                   | Default                                                             |
|---------------------|-----------------------------------------------|---------------------------------------------------------------------|
| `DATABASE_URL`      | SQLAlchemy connection URL                     | `postgresql+psycopg://customers:customers@localhost:5432/customers` |
| `CORS_ORIGINS`      | Explicitly allowed origins (JSON list)        | `[]`                                                                |
| `CORS_ORIGIN_REGEX` | Regex of allowed origins; empty in production | `localhost` / `127.0.0.1` on any port                               |
| `LOG_LEVEL`         | Log level (`DEBUG`, `INFO`, `WARNING`…)       | `INFO`                                                              |
| `DB_POOL_SIZE`      | Persistent connections in the pool            | `5`                                                                 |
| `DB_MAX_OVERFLOW`   | Extra connections allowed during peaks        | `10`                                                                |
| `POSTGRES_USER`     | PostgreSQL user (Docker Compose)              | `customers`                                                         |
| `POSTGRES_PASSWORD` | PostgreSQL password (Docker Compose)          | `customers`                                                         |
| `POSTGRES_DB`       | Database name (Docker Compose)                | `customers`                                                         |
