FROM apache/superset:4.1.1

USER root
RUN pip install --no-cache-dir psycopg2-binary
COPY superset_config.py /app/pythonpath/superset_config.py
COPY bootstrap.sh /app/bootstrap.sh
RUN chmod +x /app/bootstrap.sh
USER superset

CMD ["/app/bootstrap.sh"]
