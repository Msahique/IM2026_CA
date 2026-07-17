# CA Server image (independent). No database inside.
# Build FROM THE PROJECT ROOT (needs the shared common/ package):
#   docker build -f ca_server/Dockerfile -t im-ca-server .
#
# Config DEFAULTS ship in ca_server/variable_config.json; override any value at
# runtime with env vars or a mounted ConfigMap (env > file > default). MySQL is
# external (set IM_DB_HOST etc.).
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/    ./common/
COPY ca_server/ ./ca_server/

EXPOSE 9001
CMD ["uvicorn", "ca_server.main:app", "--host", "0.0.0.0", "--port", "9001"]
