# ETIDS Manufacturing Data Science Pipeline Stack — Revised Flow

This is a Docker Compose teaching stack for **Lecture 3: Data Wrangling & Feature Engineering** and **Lecture 4: Data Visualization & Decision Dashboard**.

The revised architecture follows this flow:

```text
Raw data
  ↓
ETL / ELT Layer
  ├─ Python / Pandas / Airflow
  ↓
Data Warehouse / Data Mart
  ├─ PostgreSQL
  ↓
Apache Superset
  ├─ Dataset
  ├─ Metric Layer
  ├─ Chart
  ├─ Dashboard
  └─ Role-based Access / Row-level Security
```

## Services

| Service | URL | Purpose |
|---|---|---|
| Next.js frontend | <http://localhost:3000> | Teaching control panel for Lectures 3 and 4 |
| FastAPI backend | <http://localhost:8000/docs> | Pipeline API, Pandas wrangling, feature-mart endpoints |
| Airflow | <http://localhost:8080> | Orchestration layer for ETL / ELT workflow |
| Apache Superset | <http://localhost:8088> | BI, metric layer, charts, dashboards, RLS lab |
| PostgreSQL | `localhost:5432` | Raw, clean, mart, and semantic registry schemas |

Default credentials:

| Tool | Username | Password |
|---|---|---|
| Airflow | `admin` | `admin` |
| Superset | `admin` | `admin` |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then run the pipeline using either route.

### Route A — FastAPI or frontend

```bash
curl -X POST http://localhost:8000/pipeline/run-all | python -m json.tool
```

Or open <http://localhost:3000> and click the pipeline buttons.

### Route B — Airflow

Open <http://localhost:8080> and trigger:

```text
etids_l3_l4_manufacturing_pipeline
```

The DAG has these teaching tasks:

1. `00_check_backend_health`
2. `01_raw_data_ingestion`
3. `02_pandas_cleaning_and_validation`
4. `03_postgresql_data_marts_and_metric_layer`
5. `04_verify_superset_datasets_metrics_charts_rls`
6. `05_publish_dashboard_readiness_report`

## Revised layer design

| Layer | Docker service / object | Main outputs |
|---|---|---|
| Raw data | `data/seed/etids_manufacturing_synthetic_dataset_v1.zip` | ERP, MES, SCADA, QMS, CMMS, logistics data |
| ETL / ELT | `backend` + `airflow` | Pandas cleaning, DQ logs, SQL mart transformations |
| Data warehouse | `postgres` | `raw`, `clean`, `mart`, `lab` schemas |
| Superset datasets | PostgreSQL views | `mart.v_dataset_oee_operational`, `mart.v_dataset_quality_decision`, `mart.v_dataset_sensor_hourly`, `mart.v_dataset_dq_governance` |
| Metric layer | PostgreSQL semantic registry | `mart.superset_metric_layer` |
| Chart layer | PostgreSQL chart registry | `mart.superset_chart_registry` |
| Dashboard layer | PostgreSQL dashboard registry | `mart.superset_dashboard_registry` |
| Access control | RLS policy registry | `mart.superset_rls_policy_registry`, `mart.superset_rls_user_plant` |

## Main API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /pipeline/ingest` | Load raw CSV data into PostgreSQL raw schema |
| `POST /pipeline/clean` | Run Pandas cleaning, standardization, validation, DQ issue logging |
| `POST /pipeline/features` | Build data marts and Superset semantic objects |
| `POST /pipeline/run-all` | Execute the full pipeline |
| `GET /pipeline/flow` | Show the revised flow |
| `GET /semantic/datasets` | Superset dataset registry |
| `GET /semantic/metrics` | Metric layer registry |
| `GET /semantic/charts` | Chart recipe registry |
| `GET /semantic/dashboards` | Dashboard registry |
| `GET /semantic/rls` | RLS policy registry |

## Superset setup sequence

After running the data pipeline, open Superset and create datasets from these objects:

```text
mart.v_dataset_oee_operational
mart.v_dataset_quality_decision
mart.v_dataset_sensor_hourly
mart.v_dataset_dq_governance
mart.v_dashboard_kpis
```

Use the semantic registries as the class exercise specification:

```sql
SELECT * FROM mart.superset_dataset_registry;
SELECT * FROM mart.superset_metric_layer;
SELECT * FROM mart.superset_chart_registry;
SELECT * FROM mart.superset_dashboard_registry;
SELECT * FROM mart.superset_rls_policy_registry;
```

Optional automatic Superset metadata creation can be attempted after the pipeline finishes:

```bash
docker compose exec superset python /app/provision/create_superset_objects.py
```

This is version-sensitive because Superset internal metadata APIs can change. The database semantic registry is the stable teaching artifact.

## Lecture 3 support

Lecture 3 emphasizes that raw data must pass quality checks, cleaning, preprocessing, EDA, and feature engineering before modeling. This stack supports that through:

- raw schema ingestion
- Pandas type conversion
- duplicate detection
- missing-value and invalid-value profiling
- impossible timestamp checks
- sensor-range checks
- DQ issue logging
- cleaned tables
- model-ready feature table: `mart.feature_quality_model`

Open:

```text
docs/lecture3_data_wrangling_lab.md
docs/revised_flow_architecture.md
docs/airflow_orchestration_lab.md
```

## Lecture 4 support

Lecture 4 moves from cleaned data to visualization, insight, decision, and action. This stack supports that through:

- dashboard-ready data marts
- Superset dataset registry
- metric layer registry
- chart recipes
- dashboard recipes
- row-level security examples
- decision dashboard lab guide

Open:

```text
docs/lecture4_dashboard_lab.md
docs/superset_semantic_dashboard_lab.md
```

## Reset

```bash
docker compose down -v
```

Then start again:

```bash
docker compose up --build
```

## Build note — Next.js `public/` directory

This revision includes an empty `frontend/public/.gitkeep` file and a Dockerfile safeguard:

```dockerfile
RUN mkdir -p public && npm run build
```

This prevents the Docker build error:

```text
COPY --from=builder /app/public ./public: "/app/public": not found
```

The `public/` directory is optional in Next.js, but Docker `COPY` requires the source path to exist.


## Airflow Login Troubleshooting

Default Airflow login:

```text
username: admin
password: admin
```

If Airflow shows `Login Failed for user: admin`, reset the user from the project folder:

```bash
docker compose exec airflow airflow users reset-password -u admin -p admin
```

If the user does not exist, create it manually:

```bash
docker compose exec airflow airflow users create -u admin -p admin -f ETIDS -l Admin -r Admin -e admin@example.com
```

Then reload `http://localhost:8080/login/` with a hard refresh. The log message `CSRF session token is missing` usually means the login page was stale after a failed login attempt; open a fresh login page before submitting again.

This patched compose file also resets the Airflow admin password automatically on container startup, so `.env` values `AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` are always applied.


## Airflow startup fix note

This build includes a corrected Airflow startup command. The earlier command split `airflow users create` across multiple shell lines, which caused Airflow to run the command without required arguments and return `ERR_EMPTY_RESPONSE` on `localhost:8080`. See `docs/airflow_startup_fix.md`.
