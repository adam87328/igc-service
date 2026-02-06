FROM python:3.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
COPY ./app /code/app
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 8081
CMD ["fastapi", "run", "app/main.py", "--port", "8081"]