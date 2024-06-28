FROM python:3.8.10-slim

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY flaskapp.wsgi .
COPY config.json .

RUN pip install -v -r requirements.txt --no-cache 
ADD website /app/website

ENTRYPOINT [ "python", "/app/main.py" ]