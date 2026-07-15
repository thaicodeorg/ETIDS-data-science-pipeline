# Superset Provisioning Notes

The PostgreSQL pipeline creates a Superset-ready semantic registry under the `mart` schema:

- `mart.superset_dataset_registry`
- `mart.superset_metric_layer`
- `mart.superset_chart_registry`
- `mart.superset_dashboard_registry`
- `mart.superset_rls_policy_registry`
- `mart.superset_rls_user_plant`

Use these objects in Superset to create the visual layer:

1. Open Superset: <http://localhost:8088>
2. Login as `admin / admin`.
3. Confirm database `ManufacturingDW` exists.
4. Create datasets from:
   - `mart.v_dataset_oee_operational`
   - `mart.v_dataset_quality_decision`
   - `mart.v_dataset_sensor_hourly`
   - `mart.v_dataset_dq_governance`
   - `mart.v_dashboard_kpis`
5. Add metrics from `mart.superset_metric_layer`.
6. Build charts from `mart.superset_chart_registry`.
7. Assemble `Manufacturing Decision Dashboard`.
8. Add RLS filters from `mart.superset_rls_policy_registry`.

The YAML file in this folder is a human-readable semantic contract for the lecture.
