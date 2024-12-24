FROM python:3.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8081

COPY ./app /code/app

WORKDIR /code/app
CMD ["uvicorn", "main:app", "--port" "8081"]