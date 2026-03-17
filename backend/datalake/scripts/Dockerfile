FROM python:3.12-slim
RUN pip install --no-cache-dir minio
COPY init_datalake.py /app/init_datalake.py
CMD ["python", "/app/init_datalake.py"]
