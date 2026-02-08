FROM python:3.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

# Environment variable for DEM tiles directory
# Default to /data/dem_tiles which should be mounted as a volume
ENV DEM_TILES_DIR=/data/dem_tiles

# Environment variables for production tuning
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV WORKER_CONNECTIONS=1000
ENV TIMEOUT=120
ENV KEEPALIVE=5

EXPOSE 8084

# Production command with gunicorn (default)
# For development, override with: fastapi run app/main.py --port 8084
CMD gunicorn app.main:app \
    --bind 0.0.0.0:8084 \
    --workers ${WORKERS} \
    --worker-class ${WORKER_CLASS} \
    --worker-connections ${WORKER_CONNECTIONS} \
    --timeout ${TIMEOUT} \
    --keepalive ${KEEPALIVE} \
    --access-logfile - \
    --error-logfile -
