"""Optional Superset object creator.

Run after the backend pipeline has created the mart schema:

    docker compose exec superset python /app/provision/create_superset_objects.py

The script is intentionally defensive because Superset's internal metadata API may
change across versions. If automatic creation fails, use the semantic registry
created in PostgreSQL and the README in this folder for manual setup.
"""
from __future__ import annotations

import json
import os
import sys

try:
    from superset.app import create_app
    from superset.extensions import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable, SqlMetric, TableColumn
    from superset.models.slice import Slice
    from superset.models.dashboard import Dashboard
except Exception as exc:  # pragma: no cover
    print(f"Superset imports failed: {exc}", file=sys.stderr)
    raise


def get_or_create_database(uri: str) -> Database:
    database = db.session.query(Database).filter_by(database_name="ManufacturingDW").one_or_none()
    if database is None:
        database = Database(database_name="ManufacturingDW", sqlalchemy_uri=uri)
        db.session.add(database)
    else:
        database.sqlalchemy_uri = uri
    db.session.commit()
    return database


def get_or_create_dataset(database: Database, table_name: str, schema: str, columns: list[str], metrics: dict[str, str]) -> SqlaTable:
    dataset = (
        db.session.query(SqlaTable)
        .filter_by(table_name=table_name, schema=schema, database_id=database.id)
        .one_or_none()
    )
    if dataset is None:
        dataset = SqlaTable(table_name=table_name, schema=schema, database=database, database_id=database.id)
        db.session.add(dataset)
        db.session.flush()
    existing_cols = {c.column_name for c in dataset.columns or []}
    for col in columns:
        if col not in existing_cols:
            db.session.add(TableColumn(table=dataset, column_name=col, type="VARCHAR"))
    existing_metrics = {m.metric_name for m in dataset.metrics or []}
    for name, expr in metrics.items():
        if name not in existing_metrics:
            db.session.add(SqlMetric(table=dataset, metric_name=name, expression=expr, description=f"ETIDS metric: {name}"))
    db.session.commit()
    return dataset


def create_chart(slice_name: str, dataset: SqlaTable, viz_type: str, params: dict) -> Slice:
    chart = db.session.query(Slice).filter_by(slice_name=slice_name).one_or_none()
    if chart is None:
        chart = Slice(
            slice_name=slice_name,
            viz_type=viz_type,
            datasource_id=dataset.id,
            datasource_type="table",
            params=json.dumps(params),
        )
        db.session.add(chart)
    else:
        chart.viz_type = viz_type
        chart.datasource_id = dataset.id
        chart.datasource_type = "table"
        chart.params = json.dumps(params)
    db.session.commit()
    return chart


def main() -> None:
    app = create_app()
    with app.app_context():
        uri = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}".format(
            user=os.getenv("POSTGRES_USER", "manufacturing"),
            password=os.getenv("POSTGRES_PASSWORD", "manufacturing"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            db=os.getenv("POSTGRES_DB", "manufacturing_dw"),
        )
        database = get_or_create_database(uri)
        oee = get_or_create_dataset(
            database,
            "v_dataset_oee_operational",
            "mart",
            ["production_date", "plant_id", "line_id", "oee", "availability", "performance", "quality", "scrap_rate", "output_quantity"],
            {
                "avg_oee": "AVG(oee)",
                "avg_availability": "AVG(availability)",
                "avg_performance": "AVG(performance)",
                "avg_quality": "AVG(quality)",
                "total_output_quantity": "SUM(output_quantity)",
                "scrap_rate": "SUM(scrap_quantity) / NULLIF(SUM(output_quantity), 0)",
            },
        )
        quality = get_or_create_dataset(
            database,
            "v_dataset_quality_decision",
            "mart",
            ["inspection_date", "plant_id", "line_id", "product_family", "defect_code", "defect_count", "sample_size", "defect_rate"],
            {"defect_rate": "SUM(defect_count) / NULLIF(SUM(sample_size), 0)", "defect_count": "SUM(defect_count)"},
        )
        dq = get_or_create_dataset(
            database,
            "v_dataset_dq_governance",
            "mart",
            ["severity", "rule_id", "table_name", "issue_count"],
            {"dq_issue_count": "SUM(issue_count)"},
        )
        charts = [
            create_chart("KPI - Average OEE", oee, "big_number_total", {"metric": "avg_oee"}),
            create_chart("Trend - OEE by production date", oee, "echarts_timeseries_line", {"metrics": ["avg_oee"], "granularity_sqla": "production_date", "time_grain_sqla": "P1D"}),
            create_chart("Bar - OEE by plant and line", oee, "echarts_bar", {"metrics": ["avg_oee"], "groupby": ["plant_id", "line_id"]}),
            create_chart("Pareto - Defect count by defect code", quality, "echarts_bar", {"metrics": ["defect_count"], "groupby": ["defect_code"]}),
            create_chart("Bar - Data quality issues by severity", dq, "echarts_bar", {"metrics": ["dq_issue_count"], "groupby": ["severity"]}),
        ]
        dashboard = db.session.query(Dashboard).filter_by(dashboard_title="Manufacturing Decision Dashboard").one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title="Manufacturing Decision Dashboard", slug="manufacturing-decision-dashboard", published=True)
            db.session.add(dashboard)
        dashboard.slices = charts
        dashboard.json_metadata = json.dumps({"label_colors": {}, "timed_refresh_immune_slices": []})
        db.session.commit()
        print("Superset datasets, metrics, charts, and dashboard metadata were created or updated.")


if __name__ == "__main__":
    main()
