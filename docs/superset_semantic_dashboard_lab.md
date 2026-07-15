# Superset Semantic Dashboard Lab

## Objective

Build a decision dashboard in Apache Superset using a formal semantic flow:

```text
Dataset -> Metric Layer -> Chart -> Dashboard -> RLS
```

## 1. Create datasets

Create Superset datasets from these PostgreSQL views:

| Dataset | Source object | Time column |
|---|---|---|
| OEE operational dataset | `mart.v_dataset_oee_operational` | `production_date` |
| Quality decision dataset | `mart.v_dataset_quality_decision` | `inspection_date` |
| Sensor hourly dataset | `mart.v_dataset_sensor_hourly` | `sensor_hour` |
| Data quality governance dataset | `mart.v_dataset_dq_governance` | none |
| Executive KPI dataset | `mart.v_dashboard_kpis` | `refreshed_at` |

## 2. Add metric layer

Use:

```sql
SELECT * FROM mart.superset_metric_layer ORDER BY dataset_name, metric_name;
```

Recommended metrics:

| Metric | Expression |
|---|---|
| `avg_oee` | `AVG(oee)` |
| `scrap_rate` | `SUM(scrap_quantity) / NULLIF(SUM(output_quantity), 0)` |
| `defect_rate` | `SUM(defect_count) / NULLIF(SUM(sample_size), 0)` |
| `dq_issue_count` | `SUM(issue_count)` |
| `max_vibration_mm_s` | `MAX(max_vibration_mm_s)` |

## 3. Build charts

Use:

```sql
SELECT * FROM mart.superset_chart_registry ORDER BY chart_name;
```

Suggested charts:

| Chart | Purpose |
|---|---|
| KPI - Average OEE | Monitor operational performance |
| Trend - OEE by production date | See performance over time |
| Bar - OEE by plant and line | Compare line performance |
| Pareto - Defect count by defect code | Prioritize quality root causes |
| Bar - Data quality issues by severity | Audit data readiness |
| Trend - Sensor vibration by hour | Detect early anomaly signals |

## 4. Assemble dashboard

Create dashboard:

```text
Manufacturing Decision Dashboard
```

Dashboard layout should follow Gestalt principles:

- group related KPI cards together
- show the most important KPI first
- avoid clutter
- use charts that match the analytical question
- keep RLS-sensitive filters visible

## 5. Role-based access and RLS

Use:

```sql
SELECT * FROM mart.superset_rls_policy_registry;
SELECT * FROM mart.superset_rls_user_plant;
```

Example RLS clause:

```sql
plant_id IN (
  SELECT plant_id
  FROM mart.superset_rls_user_plant
  WHERE username = '{{ current_username() }}'
)
```

Teaching accounts:

| Username | Role | Plant access |
|---|---|---|
| `admin` | Admin | all plants |
| `plant_p01_user` | Plant_P01_Viewer | P01 only |
| `plant_p02_user` | Plant_P02_Viewer | P02 only |
| `plant_p03_user` | Plant_P03_Viewer | P03 only |

## Submission

Students submit:

1. dashboard screenshot
2. chart selection rationale
3. metric definitions
4. RLS policy explanation
5. short decision story: what action should management take?
