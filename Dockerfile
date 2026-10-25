FROM python:3.11-slim
WORKDIR /app
COPY kaoyan_auth.py kaoyan_http_accounts.py kaoyan_http_read.py kaoyan_http_write.py kaoyan_hub_server.py kaoyan_portable.py kaoyan_repository.py kaoyan_runtime.py kaoyan_schema.py /app/
COPY kaoyan_admin_catalog.py kaoyan_admin_redaction.py /app/
COPY db_migrations /app/db_migrations
COPY index.html kaoyan_network.js kaoyan_admin.js kaoyan_admin_view.js kaoyan_admin_accounts.js kaoyan_login.js /app/
ENV KAOYAN_DB_PATH=/data/db/kaoyan_hub.sqlite3 KAOYAN_BACKUP_DIR=/data/backups KAOYAN_BIND_HOST=0.0.0.0
VOLUME ["/data/db", "/data/backups"]
CMD ["python3", "/app/kaoyan_hub_server.py"]
