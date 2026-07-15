# Superset Chart Recipe

This guide gives a minimal chart plan for Lecture 4.

## Dataset 1: `mart.v_dashboard_kpis`

Create Big Number charts:

| Metric | SQL column |
|---|---|
| Work orders | `work_orders` |
| Production runs | `production_runs` |
| Average OEE | `avg_oee` |
| Average scrap rate | `avg_scrap_rate` |
| High/medium DQ issues | `dq_issues_high_medium` |
| Average defect rate | `avg_defect_rate` |
| Late delivery rate | `late_delivery_rate` |

## Dataset 2: `mart.fact_oee_daily_line`

### OEE trend

- Chart: Line chart
- Time column: `production_date`
- Metric: average `oee`
- Series: `line_id`
- Filter: `plant_id`

### Line comparison

- Chart: Bar chart
- Dimension: `line_id`
- Metric: average `oee`
- Sort: descending average OEE

### Availability, performance, quality comparison

- Chart: Bar chart or table
- Dimensions: `plant_id`, `line_id`
- Metrics: average `availability`, average `performance`, average `quality`

## Dataset 3: `mart.fact_quality_daily`

### Defect Pareto

- Chart: Bar chart
- Dimension: `defect_code`
- Metric: sum `defect_count`
- Sort: descending defect count

### Defect rate by product family

- Chart: Bar chart
- Dimension: `product_family`
- Metric: average `defect_rate`

## Dataset 4: `mart.v_data_quality_summary`

### Data-quality issue summary

- Chart: Table or bar chart
- Dimensions: `severity`, `rule_id`, `table_name`
- Metric: sum `issue_count`

## Dashboard layout

Suggested layout:

```text
Row 1: KPI cards
Row 2: OEE trend | Line comparison
Row 3: Defect Pareto | Data-quality issue summary
Row 4: Diagnostic table
```

Use filters for plant, line, product family, and date range.
