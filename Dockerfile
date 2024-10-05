FROM python:3.12

RUN apt-get update
RUN apt-get install -y bluez bluetooth

WORKDIR /app
ADD . /app
RUN pip3 install --use-pep517 .
