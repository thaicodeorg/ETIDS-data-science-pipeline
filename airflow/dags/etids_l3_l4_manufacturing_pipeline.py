"""
ETIDS Lecture 3 and 4 manufacturing data science pipeline.

Flow:
Raw data
  -> ETL / ELT Layer: Python / Pandas / Airflow
  -> Data Warehouse / Data Mart: PostgreSQL
  -> Apache Superset: Dataset -> Metric Layer -> Chart -> Dashboard -> RLS
"""
from __future__ import annotations

from datetime import datetime, timedelta
import os
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator

BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://backend:8000")


def _post(endpoint: str) -> dict:
    url = f"{BACKEND_API_BASE_URL}{endpoint}"
    response = requests.post(url, timeout=600)
    response.raise_for_status()
    return response.json()


def _get(endpoint: str) -> dict | list:
    url = f"{BACKEND_API_BASE_URL}{endpoint}"
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.json()


def check_backend_health() -> dict:
    return _get("/health")


def ingest_raw_data() -> dict:
    # Python/Pandas logic lives in the FastAPI backend pipeline module.
    # Airflow orchestrates the step so students see the production pattern.
    return _post("/pipeline/ingest")


def clean_and_validate() -> dict:
    return _post("/pipeline/clean")


def build_data_marts_and_semantic_layer() -> dict:
    return _post("/pipeline/features")


def verify_superset_catalog() -> dict:
    datasets = _get("/semantic/datasets")
    metrics = _get("/semantic/metrics")
    charts = _get("/semantic/charts")
    rls = _get("/semantic/rls")
    return {
        "dataset_count": len(datasets),
        "metric_count": len(metrics),
        "chart_recipe_count": len(charts),
        "rls_policy_count": len(rls),
    }


def publish_dashboard_readiness_report() -> dict:
    return {
        "status": "ready_for_superset_lab",
        "open_superset": "http://localhost:8088",
        "datasets": [
            "mart.v_dataset_oee_operational",
            "mart.v_dataset_quality_decision",
            "mart.v_dataset_sensor_hourly",
            "mart.v_dataset_dq_governance",
            "mart.v_dashboard_kpis",
        ],
        "recommended_dashboard": "Manufacturing Decision Dashboard",
    }


with DAG(
    dag_id="etids_l3_l4_manufacturing_pipeline",
    description="Lecture 3 data wrangling and Lecture 4 decision dashboard pipeline.",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args={
        "owner": "etids",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["etids", "lecture3", "lecture4", "manufacturing", "superset"],
) as dag:
    t0 = PythonOperator(task_id="00_check_backend_health", python_callable=check_backend_health)
    t1 = PythonOperator(task_id="01_raw_data_ingestion", python_callable=ingest_raw_data)
    t2 = PythonOperator(task_id="02_pandas_cleaning_and_validation", python_callable=clean_and_validate)
    t3 = PythonOperator(task_id="03_postgresql_data_marts_and_metric_layer", python_callable=build_data_marts_and_semantic_layer)
    t4 = PythonOperator(task_id="04_verify_superset_datasets_metrics_charts_rls", python_callable=verify_superset_catalog)
    t5 = PythonOperator(task_id="05_publish_dashboard_readiness_report", python_callable=publish_dashboard_readiness_report)

    t0 >> t1 >> t2 >> t3 >> t4 >> t5
