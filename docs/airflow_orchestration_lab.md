# Airflow Orchestration Lab

## Objective

Use Airflow to run the Lecture 3 and Lecture 4 data pipeline as a controlled workflow.

## Steps

1. Open Airflow at <http://localhost:8080>.
2. Login with `admin / admin`.
3. Open DAG `obe03_l3_l4_manufacturing_pipeline`.
4. Trigger the DAG manually.
5. Inspect each task log.
6. Open FastAPI at <http://localhost:8000/docs> and compare API outputs.
7. Open Superset after the DAG finishes.

## DAG meaning

| Task | Lecture connection | Main output |
|---|---|---|
| `01_raw_data_ingestion` | Lecture 3 raw data stage | `raw.*` tables |
| `02_pandas_cleaning_and_validation` | Lecture 3 cleaning and validation | `clean.*`, `clean.dq_issue_log` |
| `03_postgresql_data_marts_and_metric_layer` | Lecture 3 feature engineering and Lecture 4 mart design | `mart.*` facts, views, metrics |
| `04_verify_superset_datasets_metrics_charts_rls` | Lecture 4 BI layer readiness | semantic catalog counts |
| `05_publish_dashboard_readiness_report` | Lecture 4 decision dashboard readiness | dashboard specification |

## Student questions

1. Which task is ETL and which task is ELT?
2. Why should data-quality checks run before feature engineering?
3. Why is PostgreSQL a suitable data mart for Superset?
4. Which Superset datasets should be used for OEE monitoring?
5. How does row-level security change the dashboard user experience?
