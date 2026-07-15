# ETIDS Renaming Patch Notes

This patch renames the Docker teaching project from **OBE03** to **ETIDS** to represent **Emerging Trends in Information and Data Science**.

## Scope of patch

- Project title and documentation labels changed from `OBE03` to `ETIDS`.
- Lowercase technical identifiers changed from `obe03` to `etids`.
- Docker container names changed to `etids-*`.
- Airflow DAG file and DAG ID changed to `etids_l3_l4_manufacturing_pipeline`.
- Frontend package name changed to `etids-pipeline-frontend`.
- FastAPI title and service label changed to ETIDS.
- Dataset ZIP renamed to `etids_manufacturing_synthetic_dataset_v1.zip`.
- Extracted dataset root changed to `etids_manufacturing_synthetic_dataset_v1`.
- Documentation, quickstart, Makefile, scripts, and GitHub guide updated.

## Recommended repository name

```text
etids-manufacturing-data-science-pipeline
```

## Clean rebuild after applying the patch

```powershell
docker compose down --remove-orphans -v
docker compose build --no-cache
docker compose up -d
```

## Main service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| FastAPI | http://localhost:8000/docs |
| Airflow | http://localhost:8080 |
| Superset | http://localhost:8088 |

Airflow DAG name:

```text
etids_l3_l4_manufacturing_pipeline
```
