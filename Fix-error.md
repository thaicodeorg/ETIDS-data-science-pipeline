## Error



Fix applied at pipeline.py:681-684.
Root cause: On the second run, clean_and_validate() uses Pandas to_sql(..., if_exists="replace") which internally does DROP TABLE clean.work_order. PostgreSQL blocks this because mart.v_dashboard_kpis (created by the previous run) depends on it.
Fix: Added DROP SCHEMA IF EXISTS mart CASCADE at the start of run_full_pipeline(). This drops all dependent views/tables/indexes in the mart schema before re-running, so the clean tables can be replaced without conflicts. build_feature_marts() then recreates everything from scratch.


The entire pipeline completed successfully. All 6 tasks passed:
Task	Status
00_check_backend_health	success
01_raw_data_ingestion	success
02_pandas_cleaning_and_validation	success
03_postgresql_data_marts_and_metric_layer	success
04_verify_superset_datasets_metrics_charts_rls	success
05_publish_dashboard_readiness_report	success

Root cause: clean_and_validate() tried to REPLACE tables in the clean schema, but mart schema views (like mart.v_dashboard_kpis) depended on them. PostgreSQL refused to drop the clean tables due to dependent objects.
Fix applied in backend/app/pipeline.py:244-249: Added DROP SCHEMA IF EXISTS mart CASCADE at the start of clean_and_validate() to remove dependent mart objects before replacing clean tables.