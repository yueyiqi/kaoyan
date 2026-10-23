FROM python:3.11-slim
WORKDIR /app
COPY kaoyan_hub_server.py /app/kaoyan_hub_server.py
COPY index.html /app/index.html
VOLUME ["/data/db", "/data/backups"]
EXPOSE 60231
CMD ["python3", "/app/kaoyan_hub_server.py"]
