FROM python:3.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

# Environment variable for DEM tiles directory
# Default to /data/dem_tiles which should be mounted as a volume
ENV DEM_TILES_DIR=/data/dem_tiles

EXPOSE 8084
CMD ["fastapi", "run", "app/main.py", "--port", "8084"]
