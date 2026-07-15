# Lecture 3 Lab: Data Wrangling & Feature Engineering

## Learning focus

This lab supports the Lecture 3 topics:

- data quality
- data cleaning
- preprocessing
- missing-value handling
- exploratory data analysis
- feature engineering

## Lab story

A manufacturing firm exported operational data from ERP, MES, QMS, SCADA, IIoT, and logistics systems. The records are realistic but imperfect. Students must turn raw records into trustworthy analytical tables.

## Step 1: Start the stack

```bash
docker compose up --build
```

Open:

```text
http://localhost:3000
```

## Step 2: Ingest raw data

Use the frontend button or API:

```bash
curl -X POST http://localhost:8000/pipeline/ingest
```

Expected result:

- CSV files are extracted from the dataset ZIP.
- Main files are copied to the `raw` schema.
- Sensor data is loaded as a configurable sample, controlled by `SENSOR_ROW_LIMIT`.

Inspect tables:

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'raw'
ORDER BY table_name;
```

## Step 3: Profile raw data

Example questions:

```sql
SELECT COUNT(*) FROM raw.work_order;
SELECT COUNT(*) FROM raw.production_run;
SELECT COUNT(*) FROM raw.sensor_reading;
```

Missing values:

```sql
SELECT
  COUNT(*) AS rows,
  COUNT(*) FILTER (WHERE actual_end_datetime IS NULL) AS missing_actual_end,
  COUNT(*) FILTER (WHERE operator_team_id IS NULL) AS missing_operator_team
FROM raw.work_order;
```

Duplicates:

```sql
SELECT work_order_id, COUNT(*)
FROM raw.work_order
GROUP BY work_order_id
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
```

Invalid timestamps:

```sql
SELECT work_order_id, actual_start_datetime, actual_end_datetime
FROM raw.work_order
WHERE actual_end_datetime < actual_start_datetime;
```

Sensor range checks:

```sql
SELECT *
FROM raw.sensor_reading
WHERE temperature_c::numeric < 0
   OR temperature_c::numeric > 150
   OR vibration_mm_s::numeric < 0
LIMIT 50;
```

## Step 4: Clean and validate

```bash
curl -X POST http://localhost:8000/pipeline/clean
```

Main outputs:

| Output | Purpose |
|---|---|
| `clean.work_order` | standardized work-order table |
| `clean.production_run` | typed run-level data with derived rates |
| `clean.quality_inspection` | defect-rate and high-risk labels |
| `clean.sensor_reading` | sensor-hour and sensor-validity flags |
| `clean.dq_issue_log` | data-quality issue register |

Review issue log:

```sql
SELECT severity, rule_id, table_name, COUNT(*) AS issue_count
FROM clean.dq_issue_log
GROUP BY severity, rule_id, table_name
ORDER BY issue_count DESC;
```

## Step 5: Build features

```bash
curl -X POST http://localhost:8000/pipeline/features
```

Feature outputs:

| Table / view | Meaning |
|---|---|
| `mart.fact_oee_daily_line` | daily OEE, availability, performance, quality, scrap rate |
| `mart.fact_quality_daily` | defect rate by date, product, line, and defect code |
| `mart.fact_sensor_hourly` | hourly sensor aggregates |
| `mart.fact_delivery_order` | sales and shipment delivery-risk table |
| `mart.feature_quality_model` | model-ready quality-risk feature table |
| `mart.v_data_quality_summary` | summary for data-quality dashboard |

## Step 6: Student task

Each group should submit:

1. A data-quality profile.
2. Three examples of raw-data problems.
3. A cleaning rule table.
4. A feature table design.
5. One SQL or Python EDA result.
6. A short reflection: which data-quality issue would most harm model validity?

## Suggested grading rubric

| Criterion | Score |
|---|---:|
| Correct issue identification | 25% |
| Suitable cleaning rules | 25% |
| Feature engineering logic | 25% |
| Evidence and explanation | 15% |
| Reproducibility | 10% |
