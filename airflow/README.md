# Airflow Orchestration Layer

Open Airflow at <http://localhost:8080> and trigger:

`obe03_l3_l4_manufacturing_pipeline`

The DAG implements the requested flow:

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

Airflow orchestrates the FastAPI pipeline. The heavy data wrangling is done in the backend with Python and Pandas, while SQL transformations in PostgreSQL build the data marts and Superset semantic registry.
