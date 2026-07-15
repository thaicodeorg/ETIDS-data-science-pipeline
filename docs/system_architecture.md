# System Architecture

## Design goal

The architecture supports Lecture 3 and Lecture 4 by turning the synthetic manufacturing dataset into a complete local analytics platform.

```text
Synthetic Manufacturing Dataset ZIP
        |
        v
FastAPI ETL service
        |
        v
PostgreSQL
  raw schema   -> source exports
  clean schema -> validated and standardized records
  mart schema  -> OEE, quality, sensor, delivery and dashboard marts
        |
        +--> Next.js frontend for lab control and quick inspection
        |
        +--> Apache Superset for decision dashboard design
```

## Why this architecture fits the course

Lecture 3 needs a visible, auditable path from raw data to cleaned and feature-ready tables. The backend therefore exposes each pipeline stage as a separate API call.

Lecture 4 needs BI-ready datasets and a dashboard interface. The mart schema is structured for KPI cards, trend charts, Pareto charts, comparative bar charts, and data-quality monitoring.

## Pipeline layers

| Layer | Schema / Service | Teaching role |
|---|---|---|
| Raw zone | `raw` | Shows messy source data as exported from ERP, MES, QMS, SCADA, IIoT, and logistics systems |
| Clean zone | `clean` | Demonstrates type conversion, deduplication, standardization, invalid-value handling, and issue logging |
| Feature zone | `mart` | Demonstrates analytical-base-table and feature-table design |
| Dashboard zone | `mart` + Superset | Demonstrates visual analytics and decision dashboard design |
| Application zone | FastAPI + Next.js | Demonstrates API-enabled data science workflow |

## Main services

| Component | Technology | Main responsibility |
|---|---|---|
| Database | PostgreSQL 16 | Stores raw, clean, and mart data |
| Backend | FastAPI | Runs ingestion, cleaning, validation, and feature engineering |
| Frontend | Next.js | Provides a teaching control panel and quick views |
| BI | Apache Superset | Provides dashboard construction and visual analytics lab |

## Recommended teaching flow

1. Start stack with Docker Compose.
2. Run raw ingestion.
3. Inspect `raw` tables in FastAPI, SQL, or Superset SQL Lab.
4. Run cleaning and validation.
5. Review `clean.dq_issue_log`.
6. Build feature marts.
7. Build dashboard charts in Superset.
8. Ask students to critique the dashboard using Gestalt and decision-support principles.
