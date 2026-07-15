# Airflow Startup Fix

## Symptom

Browser shows `ERR_EMPTY_RESPONSE` at `http://localhost:8080`, and Airflow logs repeat:

```text
airflow users create command error: the following arguments are required: -e/--email, -f/--firstname, -l/--lastname, -r/--role, -u/--username
```

## Root cause

The Docker Compose `command` block had the Airflow user creation command split across new lines without shell line-continuation characters. Bash treated this as:

```bash
airflow users create
--username admin
--password admin
...
```

The first command ran without arguments, so Airflow exited and Docker restarted the container repeatedly.

## Fix applied

The Airflow startup command is now single-line for the user creation/reset section:

```bash
airflow users create --username "$AIRFLOW_WWW_USER_USERNAME" --password "$AIRFLOW_WWW_USER_PASSWORD" --firstname ETIDS --lastname Admin --role Admin --email admin@example.com || airflow users reset-password -u "$AIRFLOW_WWW_USER_USERNAME" -p "$AIRFLOW_WWW_USER_PASSWORD"
```

The temporary `_PIP_ADDITIONAL_REQUIREMENTS: requests` setting was also removed to avoid the repeated startup warning. The base Airflow image already includes `requests`.

## Clean restart

```powershell
docker compose down --remove-orphans
docker volume rm ids_airflow_logs 2>$null
docker compose up --build --force-recreate airflow
```

If your project name is not `ids`, skip the volume removal command or use `docker volume ls` to find the exact name.
