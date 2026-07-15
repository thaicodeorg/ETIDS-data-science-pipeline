# OBE03 Manufacturing Business Synthetic Dataset v1.0

This package contains a realistic synthetic manufacturing-business dataset designed for the course **070125865 Emerging Trend in Information and Data Science**.

## Purpose
The dataset supports an end-to-end data science pipeline from raw industrial data to dashboards, machine learning, MLOps, federated learning, responsible AI, NLP/RAG, cloud pipelines, IoT/edge analytics, agentic AI, and blockchain traceability.

## Important note
All data are synthetic. The records imitate common structures from ERP, MES, SCADA, IIoT, QMS, CMMS, logistics, and blockchain systems. The dataset intentionally includes missing values, duplicate business keys, mixed timestamp formats, spikes, and invalid records for data wrangling and audit-style data quality control.

## Scale
- Date range: 2025-08-01 to 2026-07-31
- Plants: 3
- Lines: 6
- Machines: 36
- Products: 80
- Customers: 120
- Work-order rows: 5750
- Production-run rows: 11410
- Quality inspection rows: 11410
- Sensor readings: about 315,360 hourly rows plus duplicates
- Defect images: 240 synthetic 64x64 grayscale PNG images

## Recommended starting files
1. `00_documentation/obe03_alignment_matrix.csv` maps every OBE03 lecture to relevant files and outputs.
2. `00_documentation/data_catalog.csv` lists files, row counts, and table sizes.
3. `00_documentation/data_dictionary.csv` gives field-level information.
4. `00_documentation/entity_relationship_map.csv` gives join paths.
5. `00_documentation/data_quality_rules.csv` gives validation controls.
6. `00_documentation/scenario_ground_truth.csv` lists embedded teaching scenarios.

## Main learning zones
- `01_raw/`: messy source exports from ERP, MES, SCADA, QMS, CMMS, logistics, NLP, edge, and blockchain systems.
- `02_clean/star_schema/`: curated tables for BI and dashboarding.
- `03_features/`: model-ready feature tables for predictive maintenance, quality risk, delivery risk, MLOps, FL, fairness, and graph learning.
- `04_model_targets/`: supervised labels and data-quality issue ground truth.
- `05_dashboard/`: summary tables for Power BI, Looker Studio, or Excel dashboards.
- `06_labs/`: research cases, assignments, and exam-style questions aligned to OBE03.

## Suggested first pipeline
1. Load `01_raw/mes/work_order.csv`, `01_raw/mes/production_run.csv`, and `01_raw/qms/quality_inspection.csv`.
2. Apply rules from `00_documentation/data_quality_rules.csv`.
3. Join with `product_master`, `machine_master`, `operator_master`, and `supplier_master`.
4. Rebuild or validate `03_features/quality_risk_features.csv`.
5. Train a classification model for `high_defect_risk`.
6. Explain predictions and audit fairness using `03_features/responsible_ai_fairness_case.csv`.
7. Deploy a model mock service and monitor drift with `monitoring_reference.csv` and `monitoring_current_drifted.csv`.

## Citation and use
Use this dataset for teaching, lab exercises, and research-method demonstrations. Do not use it as evidence of any real factory performance.
