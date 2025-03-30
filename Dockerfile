FROM python:3.12-slim

RUN mkdir /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

WORKDIR /app

CMD ["bash", "entrypoint.sh"]