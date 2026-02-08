FROM python:3.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

# Environment variables for production tuning
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV WORKER_CONNECTIONS=1000
ENV TIMEOUT=120

EXPOSE 8082

# Production command with gunicorn (default)
# For development, override with: fastapi run app/main.py --port 8082
CMD gunicorn app.main:app \
    --bind 0.0.0.0:8082 \
    --workers ${WORKERS} \
    --worker-class ${WORKER_CLASS} \
    --worker-connections ${WORKER_CONNECTIONS} \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile -