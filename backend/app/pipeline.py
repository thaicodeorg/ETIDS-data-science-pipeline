from __future__ import annotations

import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import inspect, text

from .config import get_settings
from .db import begin, get_engine


@dataclass
class LoadResult:
    table: str
    rows: int
    status: str


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if math.isnan(float(obj)):
            return None
        return float(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if pd.isna(obj):
        return None
    return obj


def ensure_dataset() -> Path:
    settings = get_settings()
    root = settings.dataset_root
    if root.exists() and (root / "01_raw").exists():
        return root
    if not settings.data_zip_path.exists():
        raise FileNotFoundError(f"Dataset ZIP not found: {settings.data_zip_path}")
    settings.data_extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(settings.data_zip_path, "r") as zf:
        zf.extractall(settings.data_extract_dir)
    if not root.exists():
        # Defensive fallback if archive root name changes.
        candidates = [p for p in settings.data_extract_dir.iterdir() if p.is_dir() and "manufacturing" in p.name]
        if candidates:
            return candidates[0]
        raise FileNotFoundError("Dataset root could not be located after extraction.")
    return root


def _csv(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset file: {relative_path}")
    return path


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
        for c in df.columns
    ]
    return df


def _schema_bootstrap() -> None:
    with begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS clean"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS mart"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS lab"))


def _write_log(step: str, status: str, detail: dict[str, Any] | None = None) -> None:
    try:
        with begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO lab.pipeline_run_log(step_name, status, detail, finished_at)
                    VALUES (:step_name, :status, CAST(:detail AS jsonb), now())
                    """
                ),
                {"step_name": step, "status": status, "detail": json.dumps(_json_safe(detail or {}))},
            )
    except Exception:
        # Logging must never break the teaching pipeline.
        pass


def _load_csv_to_sql(relative_path: str, table: str, nrows: int | None = None, chunksize: int | None = None) -> LoadResult:
    root = ensure_dataset()
    path = _csv(root, relative_path)
    engine = get_engine()
    rows = 0
    if chunksize:
        first = True
        remaining = nrows
        for chunk in pd.read_csv(path, chunksize=chunksize):
            if remaining is not None:
                if remaining <= 0:
                    break
                chunk = chunk.head(remaining)
                remaining -= len(chunk)
            chunk = _normalize_columns(chunk)
            chunk.to_sql(table, engine, schema="raw", if_exists="replace" if first else "append", index=False, method="multi", chunksize=5000)
            rows += len(chunk)
            first = False
            if remaining is not None and remaining <= 0:
                break
    else:
        df = pd.read_csv(path, nrows=nrows)
        df = _normalize_columns(df)
        rows = len(df)
        df.to_sql(table, engine, schema="raw", if_exists="replace", index=False, method="multi", chunksize=5000)
    return LoadResult(table=f"raw.{table}", rows=rows, status="loaded")


def ingest_raw_data() -> dict[str, Any]:
    """Load the lecture 3/4 tables into the raw schema."""
    _schema_bootstrap()
    settings = get_settings()
    raw_map = {
        "plant_master": "01_raw/master/plant_master.csv",
        "line_master": "01_raw/master/line_master.csv",
        "machine_master": "01_raw/master/machine_master.csv",
        "product_master": "01_raw/master/product_master.csv",
        "customer_master": "01_raw/master/customer_master.csv",
        "operator_master": "01_raw/hr/operator_master.csv",
        "sales_order": "01_raw/erp/sales_order.csv",
        "work_order": "01_raw/mes/work_order.csv",
        "production_run": "01_raw/mes/production_run.csv",
        "machine_state_event": "01_raw/scada/machine_state_event.csv",
        "downtime_event": "01_raw/scada/downtime_event.csv",
        "quality_inspection": "01_raw/qms/quality_inspection.csv",
        "shipment": "01_raw/logistics/shipment.csv",
        "data_quality_rules": "01_raw/master/data_quality_rules.csv",
    }
    results: list[LoadResult] = []
    for table, rel in raw_map.items():
        results.append(_load_csv_to_sql(rel, table))
    results.append(_load_csv_to_sql("01_raw/scada/sensor_reading.csv", "sensor_reading", nrows=settings.sensor_row_limit, chunksize=50_000))
    payload = {"status": "ok", "tables": [r.__dict__ for r in results], "sensor_row_limit": settings.sensor_row_limit}
    _write_log("ingest_raw_data", "ok", payload)
    return payload


def _read_table(schema: str, table: str) -> pd.DataFrame:
    return pd.read_sql(f'SELECT * FROM "{schema}"."{table}"', get_engine())


def _to_datetime(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def _to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _make_dq_issues(work_order: pd.DataFrame, production_run: pd.DataFrame, quality: pd.DataFrame, sensor: pd.DataFrame) -> pd.DataFrame:
    issues: list[dict[str, Any]] = []

    def add(table: str, business_key: str, rule_id: str, severity: str, message: str):
        issues.append({
            "table_name": table,
            "business_key": str(business_key),
            "rule_id": rule_id,
            "severity": severity,
            "issue_message": message,
        })

    wo = _to_datetime(work_order, ["planned_start_datetime", "planned_end_datetime", "actual_start_datetime", "actual_end_datetime"])
    wo = _to_numeric(wo, ["planned_quantity", "actual_quantity", "rejected_quantity", "rework_quantity"])
    for _, r in wo[wo["work_order_id"].duplicated(keep=False)].head(500).iterrows():
        add("raw.work_order", r.get("work_order_id"), "DQ-WO-DUP", "high", "Duplicate work_order_id found.")
    bad_time = wo[wo["actual_end_datetime"].notna() & wo["actual_start_datetime"].notna() & (wo["actual_end_datetime"] <= wo["actual_start_datetime"])]
    for _, r in bad_time.head(500).iterrows():
        add("raw.work_order", r.get("work_order_id"), "DQ-WO-TIME", "high", "Actual end is not after actual start.")
    bad_qty = wo[(wo["planned_quantity"] < 0) | (wo["actual_quantity"] < 0) | (wo["rejected_quantity"] < 0)]
    for _, r in bad_qty.head(500).iterrows():
        add("raw.work_order", r.get("work_order_id"), "DQ-WO-QTY", "high", "Negative production quantity detected.")
    missing_end = wo[wo["work_order_status"].astype(str).str.lower().eq("completed") & wo["actual_end_datetime"].isna()]
    for _, r in missing_end.head(500).iterrows():
        add("raw.work_order", r.get("work_order_id"), "DQ-WO-MISSING-END", "medium", "Completed order has no actual end datetime.")

    pr = _to_datetime(production_run, ["run_start_datetime", "run_end_datetime"])
    pr = _to_numeric(pr, ["input_quantity", "output_quantity", "scrap_quantity", "runtime_minutes", "idle_minutes", "setup_minutes"])
    pr_bad_time = pr[pr["run_end_datetime"].notna() & pr["run_start_datetime"].notna() & (pr["run_end_datetime"] <= pr["run_start_datetime"])]
    for _, r in pr_bad_time.head(500).iterrows():
        add("raw.production_run", r.get("run_id"), "DQ-RUN-TIME", "high", "Run end is not after run start.")
    pr_bad_qty = pr[(pr["output_quantity"] < 0) | (pr["scrap_quantity"] < 0) | (pr["output_quantity"] > pr["input_quantity"] * 1.2)]
    for _, r in pr_bad_qty.head(500).iterrows():
        add("raw.production_run", r.get("run_id"), "DQ-RUN-QTY", "high", "Invalid or implausible run quantity detected.")

    q = _to_numeric(quality, ["sample_size", "defect_count", "measurement_1", "lower_spec_limit", "upper_spec_limit"])
    q_bad_count = q[q["defect_count"] > q["sample_size"]]
    for _, r in q_bad_count.head(500).iterrows():
        add("raw.quality_inspection", r.get("inspection_id"), "DQ-QMS-COUNT", "high", "Defect count exceeds sample size.")
    q_bad_spec = q[(q["measurement_1"] < q["lower_spec_limit"] - 5) | (q["measurement_1"] > q["upper_spec_limit"] + 5)]
    for _, r in q_bad_spec.head(500).iterrows():
        add("raw.quality_inspection", r.get("inspection_id"), "DQ-QMS-MEASURE", "medium", "Measurement is far outside specification range.")

    s = _to_numeric(sensor, ["temperature_c", "vibration_mm_s", "pressure_bar", "current_amp", "speed_rpm", "humidity_pct"])
    invalid_sensor = s[(s["temperature_c"] < 0) | (s["temperature_c"] > 150) | (s["vibration_mm_s"] < 0) | (s["pressure_bar"] < 0)]
    for _, r in invalid_sensor.head(500).iterrows():
        add("raw.sensor_reading", f"{r.get('machine_id')}@{r.get('timestamp')}", "DQ-SENSOR-RANGE", "medium", "Sensor reading violates domain range.")
    missing_sensor = s[s[["temperature_c", "vibration_mm_s", "pressure_bar", "current_amp"]].isna().any(axis=1)]
    for _, r in missing_sensor.head(500).iterrows():
        add("raw.sensor_reading", f"{r.get('machine_id')}@{r.get('timestamp')}", "DQ-SENSOR-MISSING", "low", "One or more sensor values are missing.")

    if not issues:
        issues.append({
            "table_name": "all",
            "business_key": "none",
            "rule_id": "DQ-PASS",
            "severity": "info",
            "issue_message": "No critical issues detected in the loaded sample.",
        })
    out = pd.DataFrame(issues)
    out["created_at"] = pd.Timestamp.utcnow()
    return out


def clean_and_validate() -> dict[str, Any]:
    """Build clean tables and the data-quality audit log."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS mart CASCADE"))
    work_order = _read_table("raw", "work_order")
    production_run = _read_table("raw", "production_run")
    quality = _read_table("raw", "quality_inspection")
    sensor = _read_table("raw", "sensor_reading")
    state = _read_table("raw", "machine_state_event")
    shipment = _read_table("raw", "shipment")

    # Work orders
    wo = _to_datetime(work_order, ["planned_start_datetime", "planned_end_datetime", "actual_start_datetime", "actual_end_datetime", "load_timestamp"])
    wo = _to_numeric(wo, ["planned_quantity", "actual_quantity", "rejected_quantity", "rework_quantity"])
    wo = wo.sort_values(["work_order_id", "load_timestamp"]).drop_duplicates("work_order_id", keep="last")
    wo["work_order_status"] = wo["work_order_status"].astype(str).str.strip().str.lower()
    wo["priority_level"] = wo["priority_level"].astype(str).str.strip().str.lower()
    wo["good_quantity"] = (wo["actual_quantity"] - wo["rejected_quantity"]).clip(lower=0)
    wo["yield_rate"] = wo["good_quantity"] / wo["actual_quantity"].replace({0: np.nan})
    wo["schedule_delay_minutes"] = (wo["actual_end_datetime"] - wo["planned_end_datetime"]).dt.total_seconds() / 60
    wo["production_attainment"] = wo["actual_quantity"] / wo["planned_quantity"].replace({0: np.nan})
    wo["invalid_record_flag"] = (
        wo["actual_quantity"].lt(0) | wo["planned_quantity"].lt(0) |
        (wo["actual_end_datetime"].notna() & wo["actual_start_datetime"].notna() & (wo["actual_end_datetime"] <= wo["actual_start_datetime"]))
    ).astype(int)
    wo.to_sql("work_order", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Production runs
    pr = _to_datetime(production_run, ["run_start_datetime", "run_end_datetime"])
    pr = _to_numeric(pr, ["input_quantity", "output_quantity", "scrap_quantity", "rework_quantity", "setup_minutes", "runtime_minutes", "idle_minutes", "speed_actual_ppm", "speed_standard_ppm"])
    pr = pr.drop_duplicates("run_id", keep="last")
    pr["run_status"] = pr["run_status"].astype(str).str.strip().str.lower()
    pr["good_quantity"] = (pr["output_quantity"] - pr["scrap_quantity"]).clip(lower=0)
    pr["scrap_rate"] = pr["scrap_quantity"] / pr["output_quantity"].replace({0: np.nan})
    pr["speed_ratio"] = pr["speed_actual_ppm"] / pr["speed_standard_ppm"].replace({0: np.nan})
    pr["run_date"] = pr["run_start_datetime"].dt.date
    pr.to_sql("production_run", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Quality
    q = _to_datetime(quality, ["inspection_datetime"])
    q = _to_numeric(q, ["sample_size", "defect_count", "measurement_1", "measurement_2", "lower_spec_limit", "upper_spec_limit"])
    q = q.drop_duplicates("inspection_id", keep="last")
    q["pass_fail"] = q["pass_fail"].astype(str).str.strip().str.lower()
    q["defect_code"] = q["defect_code"].astype(str).str.strip().str.upper()
    q["defect_rate"] = q["defect_count"] / q["sample_size"].replace({0: np.nan})
    q["within_spec_flag"] = q["measurement_1"].between(q["lower_spec_limit"], q["upper_spec_limit"], inclusive="both").astype(int)
    q["high_defect_risk"] = ((q["defect_rate"] >= 0.05) | q["pass_fail"].eq("fail") | q["within_spec_flag"].eq(0)).astype(int)
    q.to_sql("quality_inspection", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Sensor sample
    s = _to_datetime(sensor, ["timestamp"])
    s = _to_numeric(s, ["temperature_c", "vibration_mm_s", "pressure_bar", "current_amp", "speed_rpm", "humidity_pct"])
    s = s.drop_duplicates(["timestamp", "machine_id", "sensor_id"], keep="last")
    s["operating_state"] = s["operating_state"].astype(str).str.strip().str.upper()
    s["sensor_hour"] = s["timestamp"].dt.floor("h")
    s["sensor_valid_flag"] = (
        s["temperature_c"].between(0, 150) &
        s["vibration_mm_s"].ge(0) &
        s["pressure_bar"].ge(0) &
        s["current_amp"].ge(0)
    ).astype(int)
    s.to_sql("sensor_reading", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Machine-state events
    st = _to_datetime(state, ["event_start", "event_end"])
    st["state_code"] = st["state_code"].astype(str).str.strip().str.upper()
    st["event_duration_minutes"] = (st["event_end"] - st["event_start"]).dt.total_seconds() / 60
    st.to_sql("machine_state_event", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Shipment
    sh = _to_datetime(shipment, ["ship_date", "promised_delivery_date"])
    sh = _to_numeric(sh, ["shipped_quantity", "distance_km", "late_delivery_flag", "delay_days"])
    sh.to_sql("shipment", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    # Master data copied to clean schema.
    for table in ["plant_master", "line_master", "machine_master", "product_master", "customer_master", "operator_master", "sales_order"]:
        df = _read_table("raw", table)
        if table == "sales_order":
            df = _to_datetime(df, ["order_date", "requested_delivery_date", "promised_delivery_date", "load_timestamp"])
        df.to_sql(table, engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    dq = _make_dq_issues(work_order, production_run, quality, sensor)
    dq.to_sql("dq_issue_log", engine, schema="clean", if_exists="replace", index=False, method="multi", chunksize=5000)

    payload = {
        "status": "ok",
        "clean_tables": {
            "work_order": len(wo),
            "production_run": len(pr),
            "quality_inspection": len(q),
            "sensor_reading": len(s),
            "machine_state_event": len(st),
            "shipment": len(sh),
            "dq_issue_log": len(dq),
        },
    }
    _write_log("clean_and_validate", "ok", payload)
    return payload


def build_feature_marts() -> dict[str, Any]:
    sql = """
    CREATE SCHEMA IF NOT EXISTS mart;

    DROP TABLE IF EXISTS mart.fact_oee_daily_line;
    CREATE TABLE mart.fact_oee_daily_line AS
    WITH base AS (
        SELECT
            DATE(pr.run_start_datetime) AS production_date,
            wo.plant_id,
            wo.line_id,
            pr.machine_id,
            pr.run_id,
            pr.runtime_minutes,
            pr.idle_minutes,
            pr.setup_minutes,
            pr.output_quantity,
            pr.scrap_quantity,
            pr.good_quantity,
            pr.speed_standard_ppm,
            pr.speed_actual_ppm
        FROM clean.production_run pr
        LEFT JOIN clean.work_order wo ON pr.work_order_id = wo.work_order_id
        WHERE pr.run_start_datetime IS NOT NULL
    ), agg AS (
        SELECT
            production_date,
            plant_id,
            line_id,
            COUNT(DISTINCT run_id) AS run_count,
            COUNT(DISTINCT machine_id) AS active_machine_count,
            SUM(runtime_minutes) AS runtime_minutes,
            SUM(idle_minutes) AS idle_minutes,
            SUM(setup_minutes) AS setup_minutes,
            SUM(output_quantity) AS output_quantity,
            SUM(scrap_quantity) AS scrap_quantity,
            SUM(good_quantity) AS good_quantity,
            SUM(runtime_minutes * speed_standard_ppm) AS theoretical_output
        FROM base
        GROUP BY production_date, plant_id, line_id
    )
    SELECT
        production_date,
        plant_id,
        line_id,
        run_count,
        active_machine_count,
        runtime_minutes,
        idle_minutes,
        setup_minutes,
        output_quantity,
        scrap_quantity,
        good_quantity,
        runtime_minutes + idle_minutes + setup_minutes AS planned_production_minutes,
        runtime_minutes / NULLIF(runtime_minutes + idle_minutes + setup_minutes, 0) AS availability,
        output_quantity / NULLIF(theoretical_output, 0) AS performance,
        good_quantity / NULLIF(output_quantity, 0) AS quality,
        (runtime_minutes / NULLIF(runtime_minutes + idle_minutes + setup_minutes, 0))
        * (output_quantity / NULLIF(theoretical_output, 0))
        * (good_quantity / NULLIF(output_quantity, 0)) AS oee,
        scrap_quantity / NULLIF(output_quantity, 0) AS scrap_rate
    FROM agg;

    DROP TABLE IF EXISTS mart.fact_quality_daily;
    CREATE TABLE mart.fact_quality_daily AS
    SELECT
        DATE(q.inspection_datetime) AS inspection_date,
        wo.plant_id,
        wo.line_id,
        q.product_id,
        pm.product_family,
        q.defect_code,
        COUNT(*) AS inspection_count,
        SUM(q.sample_size) AS sample_size,
        SUM(q.defect_count) AS defect_count,
        SUM(q.defect_count)::numeric / NULLIF(SUM(q.sample_size), 0) AS defect_rate,
        AVG(q.high_defect_risk) AS high_defect_risk_rate
    FROM clean.quality_inspection q
    LEFT JOIN clean.work_order wo ON q.work_order_id = wo.work_order_id
    LEFT JOIN clean.product_master pm ON q.product_id = pm.product_id
    GROUP BY DATE(q.inspection_datetime), wo.plant_id, wo.line_id, q.product_id, pm.product_family, q.defect_code;

    DROP TABLE IF EXISTS mart.fact_sensor_hourly;
    CREATE TABLE mart.fact_sensor_hourly AS
    SELECT
        sensor_hour,
        plant_id,
        line_id,
        machine_id,
        COUNT(*) AS reading_count,
        AVG(temperature_c) AS avg_temperature_c,
        MAX(temperature_c) AS max_temperature_c,
        AVG(vibration_mm_s) AS avg_vibration_mm_s,
        MAX(vibration_mm_s) AS max_vibration_mm_s,
        AVG(pressure_bar) AS avg_pressure_bar,
        AVG(current_amp) AS avg_current_amp,
        AVG(speed_rpm) AS avg_speed_rpm,
        AVG(sensor_valid_flag) AS sensor_valid_rate
    FROM clean.sensor_reading
    GROUP BY sensor_hour, plant_id, line_id, machine_id;

    DROP TABLE IF EXISTS mart.fact_delivery_order;
    CREATE TABLE mart.fact_delivery_order AS
    SELECT
        so.sales_order_id,
        so.order_line_id,
        so.customer_id,
        so.product_id,
        so.order_date,
        so.promised_delivery_date,
        so.ordered_quantity,
        so.unit_price,
        so.discount_pct,
        so.customer_priority,
        sh.ship_date,
        sh.shipped_quantity,
        COALESCE(sh.late_delivery_flag, 0) AS late_delivery_flag,
        COALESCE(sh.delay_days, 0) AS delay_days,
        sh.root_cause,
        (so.ordered_quantity * so.unit_price * (1 - COALESCE(so.discount_pct,0)/100.0)) AS net_order_value
    FROM clean.sales_order so
    LEFT JOIN clean.shipment sh
      ON so.sales_order_id = sh.sales_order_id AND so.order_line_id = sh.order_line_id;

    DROP TABLE IF EXISTS mart.feature_quality_model;
    CREATE TABLE mart.feature_quality_model AS
    SELECT
        pr.run_id,
        pr.work_order_id,
        wo.plant_id,
        wo.line_id,
        pr.machine_id,
        wo.product_id,
        pm.product_family,
        pm.complexity_score,
        mm.machine_age_years,
        mm.criticality,
        pr.setup_minutes,
        pr.runtime_minutes,
        pr.idle_minutes,
        pr.speed_ratio,
        pr.scrap_rate,
        COALESCE(q.defect_rate, 0) AS defect_rate,
        COALESCE(q.high_defect_risk, 0) AS high_defect_risk,
        COALESCE(sh.avg_temperature_c, 0) AS avg_temperature_c,
        COALESCE(sh.max_vibration_mm_s, 0) AS max_vibration_mm_s,
        COALESCE(sh.sensor_valid_rate, 1) AS sensor_valid_rate
    FROM clean.production_run pr
    LEFT JOIN clean.work_order wo ON pr.work_order_id = wo.work_order_id
    LEFT JOIN clean.product_master pm ON wo.product_id = pm.product_id
    LEFT JOIN clean.machine_master mm ON pr.machine_id = mm.machine_id
    LEFT JOIN clean.quality_inspection q ON pr.run_id = q.run_id
    LEFT JOIN (
        SELECT DATE(sensor_hour) AS sensor_date, machine_id,
               AVG(avg_temperature_c) AS avg_temperature_c,
               MAX(max_vibration_mm_s) AS max_vibration_mm_s,
               AVG(sensor_valid_rate) AS sensor_valid_rate
        FROM mart.fact_sensor_hourly
        GROUP BY DATE(sensor_hour), machine_id
    ) sh ON sh.sensor_date = DATE(pr.run_start_datetime) AND sh.machine_id = pr.machine_id;

    CREATE OR REPLACE VIEW mart.v_data_quality_summary AS
    SELECT
        severity,
        rule_id,
        table_name,
        COUNT(*) AS issue_count
    FROM clean.dq_issue_log
    GROUP BY severity, rule_id, table_name;

    CREATE OR REPLACE VIEW mart.v_dashboard_kpis AS
    SELECT
        (SELECT COUNT(*) FROM clean.work_order) AS work_orders,
        (SELECT COUNT(*) FROM clean.production_run) AS production_runs,
        (SELECT ROUND(AVG(oee)::numeric, 4) FROM mart.fact_oee_daily_line) AS avg_oee,
        (SELECT ROUND(AVG(scrap_rate)::numeric, 4) FROM mart.fact_oee_daily_line) AS avg_scrap_rate,
        (SELECT COUNT(*) FROM clean.dq_issue_log WHERE severity IN ('high','medium')) AS dq_issues_high_medium,
        (SELECT ROUND(AVG(defect_rate)::numeric, 4) FROM mart.fact_quality_daily) AS avg_defect_rate,
        (SELECT ROUND(AVG(late_delivery_flag)::numeric, 4) FROM mart.fact_delivery_order) AS late_delivery_rate,
        now() AS refreshed_at;

    CREATE INDEX IF NOT EXISTS ix_fact_oee_daily_line_date ON mart.fact_oee_daily_line(production_date);
    CREATE INDEX IF NOT EXISTS ix_fact_quality_daily_date ON mart.fact_quality_daily(inspection_date);
    CREATE INDEX IF NOT EXISTS ix_fact_sensor_hourly_hour ON mart.fact_sensor_hourly(sensor_hour);


    -- Superset semantic layer support for Lecture 4.
    -- These objects make the BI flow explicit: Dataset -> Metric Layer -> Chart -> Dashboard -> RLS.
    CREATE OR REPLACE VIEW mart.v_dataset_oee_operational AS
    SELECT
        production_date,
        plant_id,
        line_id,
        run_count,
        active_machine_count,
        runtime_minutes,
        idle_minutes,
        setup_minutes,
        output_quantity,
        good_quantity,
        scrap_quantity,
        planned_production_minutes,
        availability,
        performance,
        quality,
        oee,
        scrap_rate
    FROM mart.fact_oee_daily_line;

    CREATE OR REPLACE VIEW mart.v_dataset_quality_decision AS
    SELECT
        inspection_date,
        plant_id,
        line_id,
        product_id,
        product_family,
        defect_code,
        inspection_count,
        sample_size,
        defect_count,
        defect_rate,
        high_defect_risk_rate
    FROM mart.fact_quality_daily;

    CREATE OR REPLACE VIEW mart.v_dataset_sensor_hourly AS
    SELECT
        sensor_hour,
        plant_id,
        line_id,
        machine_id,
        reading_count,
        avg_temperature_c,
        max_temperature_c,
        avg_vibration_mm_s,
        max_vibration_mm_s,
        avg_pressure_bar,
        avg_current_amp,
        avg_speed_rpm,
        sensor_valid_rate
    FROM mart.fact_sensor_hourly;

    CREATE OR REPLACE VIEW mart.v_dataset_dq_governance AS
    SELECT
        severity,
        rule_id,
        table_name,
        issue_count
    FROM mart.v_data_quality_summary;

    DROP TABLE IF EXISTS mart.superset_dataset_registry;
    CREATE TABLE mart.superset_dataset_registry AS
    SELECT * FROM (VALUES
        ('OEE operational dataset', 'mart.v_dataset_oee_operational', 'Line-date grain for OEE, availability, performance, quality, scrap, and output monitoring.', 'production_date', 'plant_id, line_id'),
        ('Quality decision dataset', 'mart.v_dataset_quality_decision', 'Daily quality inspection dataset for defect Pareto, defect-rate trend, and quality-risk discussion.', 'inspection_date', 'plant_id, line_id, product_family, defect_code'),
        ('Sensor hourly dataset', 'mart.v_dataset_sensor_hourly', 'Hourly IIoT sensor aggregation for visualization of operating behavior and anomaly signals.', 'sensor_hour', 'plant_id, line_id, machine_id'),
        ('Data quality governance dataset', 'mart.v_dataset_dq_governance', 'Audit-oriented summary of data quality rules, severity, and issue counts.', NULL, 'severity, rule_id, table_name'),
        ('Executive KPI dataset', 'mart.v_dashboard_kpis', 'One-row KPI view for scorecards and dashboard heading indicators.', 'refreshed_at', NULL)
    ) AS t(dataset_name, physical_object, business_description, time_column, recommended_dimensions);

    DROP TABLE IF EXISTS mart.superset_metric_layer;
    CREATE TABLE mart.superset_metric_layer AS
    SELECT * FROM (VALUES
        ('avg_oee', 'OEE operational dataset', 'AVG(oee)', 'Average overall equipment effectiveness.', 'percent'),
        ('avg_availability', 'OEE operational dataset', 'AVG(availability)', 'Average availability component of OEE.', 'percent'),
        ('avg_performance', 'OEE operational dataset', 'AVG(performance)', 'Average performance component of OEE.', 'percent'),
        ('avg_quality', 'OEE operational dataset', 'AVG(quality)', 'Average quality component of OEE.', 'percent'),
        ('total_output_quantity', 'OEE operational dataset', 'SUM(output_quantity)', 'Total production output quantity.', 'units'),
        ('scrap_rate', 'OEE operational dataset', 'SUM(scrap_quantity) / NULLIF(SUM(output_quantity), 0)', 'Scrap quantity divided by output quantity.', 'percent'),
        ('defect_rate', 'Quality decision dataset', 'SUM(defect_count) / NULLIF(SUM(sample_size), 0)', 'Overall defect rate from inspection samples.', 'percent'),
        ('defect_count', 'Quality decision dataset', 'SUM(defect_count)', 'Total number of detected defects.', 'count'),
        ('high_defect_risk_rate', 'Quality decision dataset', 'AVG(high_defect_risk_rate)', 'Average rate of high-defect-risk inspections.', 'percent'),
        ('avg_temperature_c', 'Sensor hourly dataset', 'AVG(avg_temperature_c)', 'Average operating temperature.', 'celsius'),
        ('max_vibration_mm_s', 'Sensor hourly dataset', 'MAX(max_vibration_mm_s)', 'Maximum vibration signal for anomaly monitoring.', 'mm/s'),
        ('dq_issue_count', 'Data quality governance dataset', 'SUM(issue_count)', 'Total number of logged data quality issues.', 'count')
    ) AS t(metric_name, dataset_name, sql_expression, metric_description, unit);

    DROP TABLE IF EXISTS mart.superset_chart_registry;
    CREATE TABLE mart.superset_chart_registry AS
    SELECT * FROM (VALUES
        ('KPI - Average OEE', 'big_number_total', 'OEE operational dataset', 'avg_oee', 'Executive KPI card for OEE monitoring.'),
        ('Trend - OEE by production date', 'echarts_timeseries_line', 'OEE operational dataset', 'avg_oee', 'Line chart for time-series OEE monitoring.'),
        ('Bar - OEE by plant and line', 'echarts_bar', 'OEE operational dataset', 'avg_oee', 'Comparative bar chart for line performance.'),
        ('Pareto - Defect count by defect code', 'echarts_bar', 'Quality decision dataset', 'defect_count', 'Pareto-style defect prioritization chart.'),
        ('Bar - Data quality issues by severity', 'echarts_bar', 'Data quality governance dataset', 'dq_issue_count', 'Audit-style data quality severity chart.'),
        ('Trend - Sensor vibration by hour', 'echarts_timeseries_line', 'Sensor hourly dataset', 'max_vibration_mm_s', 'Hourly IIoT anomaly-monitoring trend chart.')
    ) AS t(chart_name, superset_viz_type, dataset_name, primary_metric, decision_purpose);

    DROP TABLE IF EXISTS mart.superset_dashboard_registry;
    CREATE TABLE mart.superset_dashboard_registry AS
    SELECT * FROM (VALUES
        ('Manufacturing Decision Dashboard', 'OEE, quality, data quality, and sensor risk overview for Lecture 4.', 'KPI - Average OEE; Trend - OEE by production date; Bar - OEE by plant and line; Pareto - Defect count by defect code; Bar - Data quality issues by severity; Trend - Sensor vibration by hour', 'Production manager; quality analyst; data steward'),
        ('Lecture 3 Data Quality Audit Board', 'Data profiling, cleaning issues, and validation evidence for Lecture 3 lab reporting.', 'Bar - Data quality issues by severity', 'Student team; instructor; data steward')
    ) AS t(dashboard_name, dashboard_purpose, included_charts, target_users);

    DROP TABLE IF EXISTS mart.superset_rls_user_plant;
    CREATE TABLE mart.superset_rls_user_plant (
        username TEXT NOT NULL,
        role_name TEXT NOT NULL,
        plant_id TEXT NOT NULL,
        policy_note TEXT NOT NULL
    );
    INSERT INTO mart.superset_rls_user_plant(username, role_name, plant_id, policy_note)
    SELECT 'admin', 'Admin', plant_id, 'Administrator can see all plants.' FROM clean.plant_master
    UNION ALL SELECT 'plant_p01_user', 'Plant_P01_Viewer', 'P01', 'Teaching RLS example: user can see only Plant P01.'
    UNION ALL SELECT 'plant_p02_user', 'Plant_P02_Viewer', 'P02', 'Teaching RLS example: user can see only Plant P02.'
    UNION ALL SELECT 'plant_p03_user', 'Plant_P03_Viewer', 'P03', 'Teaching RLS example: user can see only Plant P03.';

    DROP TABLE IF EXISTS mart.superset_rls_policy_registry;
    CREATE TABLE mart.superset_rls_policy_registry AS
    SELECT * FROM (VALUES
        ('RLS - Plant scoped access', 'OEE operational dataset', 'plant_id IN (SELECT plant_id FROM mart.superset_rls_user_plant WHERE username = ''{{ current_username() }}'')', 'Restricts OEE records to plants mapped to the current Superset username.'),
        ('RLS - Plant scoped quality access', 'Quality decision dataset', 'plant_id IN (SELECT plant_id FROM mart.superset_rls_user_plant WHERE username = ''{{ current_username() }}'')', 'Restricts quality records to plants mapped to the current Superset username.'),
        ('RLS - Plant scoped sensor access', 'Sensor hourly dataset', 'plant_id IN (SELECT plant_id FROM mart.superset_rls_user_plant WHERE username = ''{{ current_username() }}'')', 'Restricts sensor records to plants mapped to the current Superset username.')
    ) AS t(policy_name, dataset_name, sql_clause, policy_description);

    CREATE INDEX IF NOT EXISTS ix_rls_user_plant_username ON mart.superset_rls_user_plant(username);
    """
    with begin() as conn:
        conn.execute(text(sql))
    counts = {}
    for schema, table in [
        ("mart", "fact_oee_daily_line"),
        ("mart", "fact_quality_daily"),
        ("mart", "fact_sensor_hourly"),
        ("mart", "fact_delivery_order"),
        ("mart", "feature_quality_model"),
        ("mart", "superset_dataset_registry"),
        ("mart", "superset_metric_layer"),
        ("mart", "superset_chart_registry"),
        ("mart", "superset_dashboard_registry"),
        ("mart", "superset_rls_user_plant"),
    ]:
        counts[f"{schema}.{table}"] = int(pd.read_sql(f"SELECT COUNT(*) AS n FROM {schema}.{table}", get_engine())["n"].iloc[0])
    payload = {"status": "ok", "mart_tables": counts}
    _write_log("build_feature_marts", "ok", payload)
    return payload


def run_full_pipeline() -> dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS mart CASCADE"))
    return {
        "ingest": ingest_raw_data(),
        "clean": clean_and_validate(),
        "marts": build_feature_marts(),
    }


def list_tables() -> dict[str, list[str]]:
    inspector = inspect(get_engine())
    result: dict[str, list[str]] = {}
    for schema in ["raw", "clean", "mart", "lab"]:
        try:
            result[schema] = sorted(inspector.get_table_names(schema=schema) + inspector.get_view_names(schema=schema))
        except Exception:
            result[schema] = []
    return result


def query_dataframe(sql: str, limit: int = 200) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 2000))
    df = pd.read_sql(f"{sql} LIMIT {safe_limit}", get_engine())
    df = df.replace({np.nan: None})
    return _json_safe(df.to_dict(orient="records"))
