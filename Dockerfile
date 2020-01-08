FROM python:3.8-alpine
WORKDIR /app

ADD requirements.txt .
ADD . .

RUN pip install -r requirements.txt