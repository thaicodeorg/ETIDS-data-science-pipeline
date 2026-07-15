$UserName = if ($env:AIRFLOW_ADMIN_USERNAME) { $env:AIRFLOW_ADMIN_USERNAME } else { "admin" }
$UserPass = if ($env:AIRFLOW_ADMIN_PASSWORD) { $env:AIRFLOW_ADMIN_PASSWORD } else { "admin" }

docker compose exec airflow airflow users reset-password -u $UserName -p $UserPass
if ($LASTEXITCODE -ne 0) {
  docker compose exec airflow airflow users create -u $UserName -p $UserPass -f ETIDS -l Admin -r Admin -e admin@example.com
}
Write-Host "Airflow admin user is ready: $UserName / $UserPass"
