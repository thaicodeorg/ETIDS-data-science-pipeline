from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .pipeline import (
    build_feature_marts,
    clean_and_validate,
    ingest_raw_data,
    list_tables,
    query_dataframe,
    run_full_pipeline,
)

settings = get_settings()

app = FastAPI(
    title="ETIDS Manufacturing Data Science Pipeline API",
    version="1.0.0",
    description="FastAPI backend for Lecture 3 data wrangling and Lecture 4 dashboard labs.",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "etids-pipeline-api"}


@app.post("/pipeline/ingest")
def ingest():
    try:
        return ingest_raw_data()
    except Exception as exc:  # pragma: no cover - teaching API surface
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/pipeline/clean")
def clean():
    try:
        return clean_and_validate()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/pipeline/features")
def features():
    try:
        return build_feature_marts()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/pipeline/run-all")
def run_all():
    try:
        return run_full_pipeline()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metadata/tables")
def metadata_tables():
    return list_tables()


@app.get("/semantic/datasets")
def semantic_datasets(limit: int = Query(default=100, ge=1, le=1000)):
    return query_dataframe(
        """
        SELECT dataset_name, physical_object, business_description, time_column, recommended_dimensions
        FROM mart.superset_dataset_registry
        ORDER BY dataset_name
        """,
        limit=limit,
    )


@app.get("/semantic/metrics")
def semantic_metrics(limit: int = Query(default=200, ge=1, le=1000)):
    return query_dataframe(
        """
        SELECT metric_name, dataset_name, sql_expression, metric_description, unit
        FROM mart.superset_metric_layer
        ORDER BY dataset_name, metric_name
        """,
        limit=limit,
    )


@app.get("/semantic/charts")
def semantic_charts(limit: int = Query(default=200, ge=1, le=1000)):
    return query_dataframe(
        """
        SELECT chart_name, superset_viz_type, dataset_name, primary_metric, decision_purpose
        FROM mart.superset_chart_registry
        ORDER BY chart_name
        """,
        limit=limit,
    )


@app.get("/semantic/dashboards")
def semantic_dashboards(limit: int = Query(default=100, ge=1, le=1000)):
    return query_dataframe(
        """
        SELECT dashboard_name, dashboard_purpose, included_charts, target_users
        FROM mart.superset_dashboard_registry
        ORDER BY dashboard_name
        """,
        limit=limit,
    )


@app.get("/semantic/rls")
def semantic_rls(limit: int = Query(default=200, ge=1, le=1000)):
    return query_dataframe(
        """
        SELECT policy_name, dataset_name, sql_clause, policy_description
        FROM mart.superset_rls_policy_registry
        ORDER BY policy_name
        """,
        limit=limit,
    )


@app.get("/pipeline/flow")
def pipeline_flow():
    return {
        "flow": [
            "Raw data",
            "ETL / ELT Layer: Python, Pandas, Airflow",
            "Data Warehouse / Data Mart: PostgreSQL raw, clean, mart schemas",
            "Apache Superset: Dataset, Metric Layer, Chart, Dashboard, Role-based Access / Row-level Security",
        ],
        "airflow_dag": "etids_l3_l4_manufacturing_pipeline",
        "api_sequence": [
            "POST /pipeline/ingest",
            "POST /pipeline/clean",
            "POST /pipeline/features",
        ],
        "superset_semantic_objects": [
            "mart.superset_dataset_registry",
            "mart.superset_metric_layer",
            "mart.superset_chart_registry",
            "mart.superset_dashboard_registry",
            "mart.superset_rls_policy_registry",
        ],
    }


@app.get("/quality/summary")
def quality_summary(limit: int = Query(default=200, ge=1, le=2000)):
    return query_dataframe(
        """
        SELECT severity, rule_id, table_name, issue_count
        FROM mart.v_data_quality_summary
        ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END,
                 issue_count DESC
        """,
        limit=limit,
    )


@app.get("/quality/issues")
def quality_issues(limit: int = Query(default=100, ge=1, le=2000)):
    return query_dataframe(
        """
        SELECT table_name, business_key, rule_id, severity, issue_message, created_at
        FROM clean.dq_issue_log
        ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END,
                 created_at DESC
        """,
        limit=limit,
    )


@app.get("/dashboard/kpis")
def dashboard_kpis():
    rows = query_dataframe("SELECT * FROM mart.v_dashboard_kpis", limit=1)
    return rows[0] if rows else {}


@app.get("/dashboard/oee-daily")
def oee_daily(limit: int = Query(default=200, ge=1, le=2000)):
    return query_dataframe(
        """
        SELECT production_date, plant_id, line_id,
               ROUND(oee::numeric, 4) AS oee,
               ROUND(availability::numeric, 4) AS availability,
               ROUND(performance::numeric, 4) AS performance,
               ROUND(quality::numeric, 4) AS quality,
               ROUND(scrap_rate::numeric, 4) AS scrap_rate,
               run_count, output_quantity, good_quantity
        FROM mart.fact_oee_daily_line
        ORDER BY production_date DESC, plant_id, line_id
        """,
        limit=limit,
    )


@app.get("/dashboard/defect-pareto")
def defect_pareto(limit: int = Query(default=50, ge=1, le=2000)):
    return query_dataframe(
        """
        SELECT defect_code,
               SUM(defect_count) AS defect_count,
               SUM(sample_size) AS sample_size,
               ROUND((SUM(defect_count)::numeric / NULLIF(SUM(sample_size),0)), 4) AS defect_rate
        FROM mart.fact_quality_daily
        GROUP BY defect_code
        ORDER BY defect_count DESC
        """,
        limit=limit,
    )


@app.get("/dashboard/line-performance")
def line_performance(limit: int = Query(default=100, ge=1, le=2000)):
    return query_dataframe(
        """
        SELECT plant_id, line_id,
               ROUND(AVG(oee)::numeric, 4) AS avg_oee,
               ROUND(AVG(scrap_rate)::numeric, 4) AS avg_scrap_rate,
               SUM(output_quantity) AS output_quantity,
               SUM(good_quantity) AS good_quantity,
               COUNT(*) AS production_days
        FROM mart.fact_oee_daily_line
        GROUP BY plant_id, line_id
        ORDER BY avg_oee DESC
        """,
        limit=limit,
    )


@app.get("/lab/lecture3")
def lecture3_map():
    return {
        "lecture": "Lecture 3: Data Wrangling & Feature Engineering",
        "pipeline_stages": ["raw data", "quality check", "cleaning", "preprocessing", "EDA", "feature engineering"],
        "api_sequence": ["POST /pipeline/ingest", "POST /pipeline/clean", "POST /pipeline/features"],
        "main_tables": ["raw.*", "clean.dq_issue_log", "clean.work_order", "clean.production_run", "mart.feature_quality_model"],
        "student_outputs": ["data quality profile", "cleaning rule explanation", "feature table design", "short lab report"],
    }


@app.get("/lab/lecture4")
def lecture4_map():
    return {
        "lecture": "Lecture 4: Data Visualization & Decision Dashboard",
        "workflow": ["raw data", "cleaned data", "visualization", "insight", "decision", "action"],
        "superset_datasets": ["mart.v_dashboard_kpis", "mart.fact_oee_daily_line", "mart.fact_quality_daily", "mart.v_data_quality_summary"],
        "recommended_charts": ["KPI cards", "line chart", "bar chart", "Pareto chart", "heatmap/table"],
        "student_outputs": ["decision dashboard", "chart choice justification", "Gestalt critique", "dashboard presentation"],
    }
