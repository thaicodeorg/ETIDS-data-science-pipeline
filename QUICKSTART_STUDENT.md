# ETIDS Docker Lab: Student Quick Start

This project supports ETIDS Lecture 3 and Lecture 4 labs.

- Lecture 3: data wrangling, data quality, cleaning, preprocessing, EDA, feature engineering.
- Lecture 4: Superset datasets, metric layer, charts, dashboards, role-based access, and row-level security.

## 1. Install prerequisites

Install these before class:

1. Docker Desktop
2. Git
3. A terminal: PowerShell on Windows, Terminal on macOS/Linux
4. A browser: Edge, Chrome, or Firefox

## 2. Clone the project

```bash
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>
```

## 3. Create environment file

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

## 4. Start the lab stack

```bash
docker compose up -d --build
```

First startup may take several minutes.

## 5. Open services

| Service | URL | Login |
|---|---|---|
| Frontend | <http://localhost:3000> | none |
| FastAPI docs | <http://localhost:8000/docs> | none |
| Airflow | <http://localhost:8080> | admin / admin |
| Superset | <http://localhost:8088> | admin / admin |

## 6. Run the pipeline

Option A: Use FastAPI:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/run-all
```

Option B: Use Airflow:

1. Open <http://localhost:8080>
2. Login as `admin / admin`
3. Search for `etids_l3_l4_manufacturing_pipeline`
4. Click **Trigger DAG**

## 7. Check database outputs

```bash
docker compose exec postgres psql -U manufacturing -d manufacturing_dw -c "\dt mart.*"
```

Expected outputs include:

- `mart.fact_oee_daily_line`
- `mart.fact_quality_daily`
- `mart.fact_sensor_hourly`
- `mart.v_dashboard_kpis`
- `mart.v_data_quality_summary`

## 8. Stop the lab

```bash
docker compose down
```

To remove database volumes and reset everything:

```bash
docker compose down -v
```

## 9. Common fixes

### Port already used

Edit `.env` and change ports, for example:

```text
FRONTEND_PORT=3001
BACKEND_PORT=8001
AIRFLOW_PORT=8081
SUPERSET_PORT=8089
```

### Airflow login fails

```bash
docker compose exec airflow airflow users reset-password -u admin -p admin
```

### Superset has no data

Run the pipeline first, then refresh datasets.

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/run-all
```
