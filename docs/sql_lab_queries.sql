-- Lecture 3: raw table counts
SELECT 'work_order' AS table_name, COUNT(*) AS row_count FROM raw.work_order
UNION ALL
SELECT 'production_run', COUNT(*) FROM raw.production_run
UNION ALL
SELECT 'quality_inspection', COUNT(*) FROM raw.quality_inspection
UNION ALL
SELECT 'sensor_reading', COUNT(*) FROM raw.sensor_reading;

-- Lecture 3: data-quality summary
SELECT severity, rule_id, table_name, COUNT(*) AS issue_count
FROM clean.dq_issue_log
GROUP BY severity, rule_id, table_name
ORDER BY issue_count DESC;

-- Lecture 3: feature table preview
SELECT *
FROM mart.feature_quality_model
LIMIT 100;

-- Lecture 4: executive KPI row
SELECT * FROM mart.v_dashboard_kpis;

-- Lecture 4: OEE trend
SELECT production_date, plant_id, line_id, oee, availability, performance, quality, scrap_rate
FROM mart.fact_oee_daily_line
ORDER BY production_date, plant_id, line_id;

-- Lecture 4: defect Pareto
SELECT defect_code, SUM(defect_count) AS defect_count
FROM mart.fact_quality_daily
GROUP BY defect_code
ORDER BY defect_count DESC;
