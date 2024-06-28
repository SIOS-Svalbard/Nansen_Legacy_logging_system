FROM python:3.8-slim AS builder

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY flaskapp.wsgi .
# COPY config.json .

RUN apt-get clean
RUN apt-get update \ 
    && apt-get -y install libpq-dev gcc rsync\
    && pip install -v -r requirements.txt \
    && rm -rf /root/.cache
RUN mkdir -p /folder_to_copy/usr/local/lib/python3.8/site-packages \ 
    && rsync -a  /usr/local/lib/python3.8/site-packages /folder_to_copy/usr/local/lib/python3.8 \
    && rsync -a /usr/local/bin /folder_to_copy/usr/local \
    && rsync -a /usr/bin /folder_to_copy/usr \
    && rsync -a /usr/lib /folder_to_copy/usr

ADD website /app/website


FROM python:3.8-slim

WORKDIR /app
COPY --from=builder /app .
COPY --from=builder /folder_to_copy /

# RUN pytest /app/tests/

ENTRYPOINT [ "python", "/app/main.py" ]