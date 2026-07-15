# Lecture 4 Lab: Data Visualization & Decision Dashboard

## Learning focus

This lab supports the Lecture 4 topics:

- visual perception
- pre-attentive processing
- Gestalt principles
- chart selection
- BI tools
- dashboard design for decision support

## Lab story

Management wants a dashboard to monitor manufacturing performance. The dashboard must help users move from data to insight, decision, and action.

## Step 1: Run the full pipeline

```bash
curl -X POST http://localhost:8000/pipeline/run-all
```

## Step 2: Open Superset

```text
http://localhost:8088
```

Login:

```text
username: admin
password: admin
```

The database connection should appear as:

```text
ManufacturingDW
```

## Step 3: Create Superset datasets

Create datasets from these objects:

```text
mart.v_dashboard_kpis
mart.fact_oee_daily_line
mart.fact_quality_daily
mart.v_data_quality_summary
mart.fact_sensor_hourly
mart.fact_delivery_order
```

## Step 4: Build dashboard page 1: Executive overview

Recommended charts:

| Dashboard area | Dataset | Chart type | Purpose |
|---|---|---|---|
| Top KPI row | `mart.v_dashboard_kpis` | Big number | Show OEE, scrap, defect, DQ issue status |
| OEE trend | `mart.fact_oee_daily_line` | Line chart | Monitor trend over time |
| Line comparison | `mart.fact_oee_daily_line` | Bar chart | Compare production lines |
| Defect Pareto | `mart.fact_quality_daily` | Bar chart | Identify top defect types |
| DQ issue summary | `mart.v_data_quality_summary` | Table or bar chart | Show reliability of the data source |

## Step 5: Build dashboard page 2: Diagnostic view

Recommended charts:

| Chart | Analytical question |
|---|---|
| OEE by line and date | Which line is unstable? |
| Defect rate by product family | Which products need quality review? |
| Sensor valid rate by machine | Which machines have data-collection risk? |
| Late delivery by root cause | Is delay caused by production, quality, material, or logistics? |
| Data-quality issue table | Which records should be audited first? |

## Step 6: Design critique checklist

Students should check the dashboard using these principles:

| Principle | Audit question |
|---|---|
| Figure-ground | Do the main KPIs stand out from decoration? |
| Similarity | Are related metrics encoded consistently? |
| Proximity | Are related charts placed near each other? |
| Common region | Are KPI, trend, and diagnostic sections clearly grouped? |
| Continuity | Does the eye move from overview to diagnosis to action? |
| Focal point | Is the most important risk visible within 5 seconds? |
| Working memory | Does the dashboard avoid forcing users to remember numbers from another page? |

## Step 7: Decision statement

Each group should end with one decision statement:

```text
Based on the dashboard, management should take [action] because [evidence].
```

Example:

```text
Management should prioritize root-cause analysis on Line L03 because its OEE is below the plant average while defect and sensor-validity risks are higher than peer lines.
```

## Deliverables

1. Superset dashboard screenshot.
2. Chart selection table.
3. Dashboard design critique.
4. One decision recommendation.
5. Short oral presentation.
