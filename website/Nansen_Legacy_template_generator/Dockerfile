FROM python:3.8.10-slim

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY flaskapp.wsgi .
COPY update-config.py .
# COPY config.json .

RUN apt-get clean
RUN pip install -v -r requirements.txt

ADD website /app/website

ENTRYPOINT [ "python", "/app/main.py" ]