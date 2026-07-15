up:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v

run-api:
	curl -X POST http://localhost:8000/pipeline/run-all | python -m json.tool

flow:
	curl http://localhost:8000/pipeline/flow | python -m json.tool

semantic:
	curl http://localhost:8000/semantic/datasets | python -m json.tool
	curl http://localhost:8000/semantic/metrics | python -m json.tool

airflow:
	@echo "Open http://localhost:8080 and trigger DAG: etids_l3_l4_manufacturing_pipeline"


airflow-reset-admin:
	docker compose exec airflow airflow users reset-password -u $${AIRFLOW_ADMIN_USERNAME:-admin} -p $${AIRFLOW_ADMIN_PASSWORD:-admin} || docker compose exec airflow airflow users create -u $${AIRFLOW_ADMIN_USERNAME:-admin} -p $${AIRFLOW_ADMIN_PASSWORD:-admin} -f ETIDS -l Admin -r Admin -e admin@example.com
