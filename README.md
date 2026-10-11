# DataSentinel

Real-Time Financial Data Pipeline & Observability Platform.

## Architecture

```
Kafka Producer → Kafka Topic → Kafka Consumer → PostgreSQL
                                                     ↓
                                              Airflow DAGs
                                     (Aggregation + DQ Checks)
                                                     ↓
                                            FastAPI Backend
                                                     ↓
                                           React Dashboard
```

| Layer | Technology |
|---|---|
| Event streaming | Apache Kafka (Confluent) |
| Orchestration | Apache Airflow 2.9 |
| Storage | PostgreSQL 16 (BigQuery in production) |
| Backend | FastAPI + SQLAlchemy (async) |
| Auth | JWT (access + refresh tokens) |
| Frontend | React 18 + Vite + TailwindCSS + Recharts |
| Containerisation | Docker Compose |
| CI/CD | GitHub Actions |

## Monorepo Structure

```
DataSentinel/
├── backend/          # FastAPI application
├── frontend/         # React + Vite SPA
├── airflow/
│   └── dags/         # Aggregation + DQ DAGs
├── kafka/            # Producer + Consumer scripts
├── scripts/          # DB init SQL
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Local Setup

### Prerequisites
- Docker Desktop ≥ 4.x
- `docker compose` CLI plugin

### 1. Clone and configure

```bash
git clone <repo-url>
cd DataSentinel
cp .env.example .env
# Edit .env — set a strong SECRET_KEY and POSTGRES_PASSWORD at minimum
```

### 2. Start all services

```bash
docker compose up --build
```

Services started:
| Service | URL |
|---|---|
| React frontend | http://localhost:3000 |
| FastAPI backend | http://localhost:8000/docs |
| Airflow UI | http://localhost:8080 (admin/admin) |
| PostgreSQL | localhost:5432 |

### 3. Create your first user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","username":"admin","password":"secret","role":"admin"}'
```

### 4. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret"}'
```

The Kafka producer starts automatically at 5 events/second. Transactions appear in PostgreSQL within seconds and are visible on the dashboard.

## Airflow Connections

In the Airflow UI (http://localhost:8080), add a Postgres connection:

| Field | Value |
|---|---|
| Conn Id | `datasentinel_postgres` |
| Conn Type | Postgres |
| Host | `postgres` |
| Database | `datasentinel` |
| Login | `datasentinel` |
| Password | *(from .env)* |
| Port | `5432` |

## API Reference

All protected endpoints require `Authorization: Bearer <access_token>`.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register user |
| POST | `/auth/login` | — | Login, returns tokens |
| POST | `/auth/refresh` | — | Refresh access token |
| GET | `/auth/me` | user | Current user info |
| GET | `/pipeline/runs` | user | DAG run history |
| GET | `/pipeline/stats` | user | Live pipeline stats |
| GET | `/dq/metrics` | user | DQ check results |
| POST | `/admin/trigger-dag` | admin | Trigger Airflow DAG |
| GET | `/admin/alerts` | admin | Alert history |
| PATCH | `/admin/alerts/{id}/resolve` | admin | Resolve alert |

## Running Tests

```bash
# Backend
cd backend
pip install -r requirements.txt aiosqlite pytest-asyncio httpx
pytest

# Frontend
cd frontend
npm install
npm test
```

## Configuration Reference

All configuration is via environment variables. See [.env.example](.env.example) for the full list.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | dev key | JWT signing secret — **change in production** |
| `POSTGRES_PASSWORD` | changeme | PostgreSQL password |
| `PRODUCER_RATE_PER_SECOND` | 5 | Kafka producer event rate |
| `ALERT_EMAIL` | — | Destination for DQ failure emails |

## GCP Production Deployment

> Local PostgreSQL → **BigQuery**
> Local Kafka → **Google Cloud Pub/Sub** or **Confluent Cloud**
> Local Airflow → **Cloud Composer 2**

### Steps

1. **BigQuery**: Replace the consumer's `psycopg2` writes with the `google-cloud-bigquery` client. Point Airflow DAGs at BigQuery tables using `BigQueryInsertJobOperator`.

2. **Cloud Composer**: Upload DAGs from `airflow/dags/` to the Composer environment bucket:
   ```bash
   gsutil cp airflow/dags/*.py gs://<composer-bucket>/dags/
   ```

3. **Cloud Run (Backend)**:
   ```bash
   gcloud run deploy datasentinel-backend \
     --source backend/ \
     --set-env-vars SECRET_KEY=... \
     --region us-central1
   ```

4. **Firebase Hosting or Cloud Run (Frontend)**:
   ```bash
   npm run build
   gcloud run deploy datasentinel-frontend --source frontend/
   ```

5. **Secret Manager**: Store all secrets (`SECRET_KEY`, DB credentials, SMTP) in Google Secret Manager and reference them from Cloud Run via `--set-secrets`.

6. **IAM**: Assign `roles/bigquery.dataEditor` to the Cloud Run service account for the backend, and `roles/bigquery.dataViewer` for read-only paths.
