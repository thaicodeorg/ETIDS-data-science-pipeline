# ETIDS Manufacturing Data Science Pipeline

Docker-based teaching project for **ETIDS Emerging Trends in Information and Data Science**.

This project supports:

- **Lecture 3:** Data Wrangling & Feature Engineering
- **Lecture 4:** Data Visualization & Decision Dashboard

It provides a full lab stack:

```text
Raw manufacturing data
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

## 1. Services

| Service | URL | Purpose |
|---|---|---|
| Frontend | <http://localhost:3000> | Student control panel |
| FastAPI | <http://localhost:8000/docs> | Pipeline API |
| Airflow | <http://localhost:8080> | Workflow orchestration |
| Superset | <http://localhost:8088> | Dashboard and BI layer |
| PostgreSQL | `localhost:5432` | Warehouse and data mart |

Default logins:

| Tool | Username | Password |
|---|---|---|
| Airflow | `admin` | `admin` |
| Superset | `admin` | `admin` |

## 2. Quick start for students

```bash
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>
cp .env.example .env
docker compose up -d --build
```

Windows PowerShell:

```powershell
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>
Copy-Item .env.example .env
docker compose up -d --build
```

Open the frontend:

```text
http://localhost:3000
```

## 3. Run the data pipeline

FastAPI option:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/run-all
```

Airflow option:

1. Open <http://localhost:8080>
2. Login with `admin / admin`
3. Search for `etids_l3_l4_manufacturing_pipeline`
4. Click **Trigger DAG**
5. Check task logs and DAG graph

## 4. Check PostgreSQL outputs

```bash
docker compose exec postgres psql -U manufacturing -d manufacturing_dw -c "\dt mart.*"
```

Expected data mart objects:

- `mart.fact_oee_daily_line`
- `mart.fact_quality_daily`
- `mart.fact_sensor_hourly`
- `mart.v_dashboard_kpis`
- `mart.v_data_quality_summary`

## 5. Superset dashboard workflow

In Superset, create datasets from the `mart` schema.

Recommended datasets:

- `mart.v_dashboard_kpis`
- `mart.fact_oee_daily_line`
- `mart.fact_quality_daily`
- `mart.fact_sensor_hourly`
- `mart.v_data_quality_summary`

Recommended dashboard:

```text
ETIDS Manufacturing Decision Dashboard
```

Recommended charts:

| Chart | Dataset | Type |
|---|---|---|
| Overall OEE | `fact_oee_daily_line` | Big Number |
| OEE Trend | `fact_oee_daily_line` | Line Chart |
| OEE by Plant | `fact_oee_daily_line` | Bar Chart |
| Defect Pareto | `fact_quality_daily` | Bar Chart |
| Sensor Trend | `fact_sensor_hourly` | Line Chart |
| Data Quality Issues | `v_data_quality_summary` | Bar / Table |

## 6. Important documents

| File | Purpose |
|---|---|
| `QUICKSTART_STUDENT.md` | Short student installation guide |
| `docs/lecture3_data_wrangling_lab.md` | Lecture 3 lab guide |
| `docs/lecture4_dashboard_lab.md` | Lecture 4 lab guide |
| `docs/airflow_orchestration_lab.md` | Airflow tutorial |
| `docs/superset_semantic_dashboard_lab.md` | Superset tutorial |
| `docs/github/INSTRUCTOR_GITHUB_PUBLISHING_GUIDE.md` | How to publish to GitHub |

## 7. Troubleshooting

### Airflow login problem

```bash
docker compose exec airflow airflow users reset-password -u admin -p admin
```

### Superset has no data

Run the pipeline first:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/run-all
```

### Port conflict

Edit `.env` and change ports:

```text
FRONTEND_PORT=3001
BACKEND_PORT=8001
AIRFLOW_PORT=8081
SUPERSET_PORT=8089
```

### Reset everything

```bash
docker compose down -v
docker compose up -d --build
```

## 8. License

MIT License. Use for teaching and research.
