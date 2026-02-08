FROM python:3.13
WORKDIR /code

# Copy app first to get igc_lib requirements
COPY ./app /code/app
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Environment variables for production tuning
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV WORKER_CONNECTIONS=1000
ENV TIMEOUT=120

EXPOSE 8081

# Production command with gunicorn (default)
# For development, override with: fastapi run app/main.py --port 8081
CMD gunicorn app.main:app \
    --bind 0.0.0.0:8081 \
    --workers ${WORKERS} \
    --worker-class ${WORKER_CLASS} \
    --worker-connections ${WORKER_CONNECTIONS} \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile -