"""Teaching note for the ETL/ELT layer.

The executable Pandas transformations are implemented in backend/app/pipeline.py so
FastAPI and Airflow share one source of truth. This file is intentionally small and
points students to the production pattern: reusable Python functions orchestrated by
Airflow and exposed through an API.
"""

PIPELINE_STEPS = [
    "ingest_raw_data: load source files into PostgreSQL raw schema",
    "clean_and_validate: use Pandas for typing, deduplication, missing-value handling, and DQ issue logging",
    "build_feature_marts: use PostgreSQL ELT to create mart tables, Superset datasets, metric registry, chart registry, dashboard registry, and RLS policy registry",
]
