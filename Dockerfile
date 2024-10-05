FROM python:3.12

WORKDIR /app
ADD . /app
RUN pip3 install --use-pep517 .
