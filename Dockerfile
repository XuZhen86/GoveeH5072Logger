FROM python:3.10-alpine

WORKDIR /app
ADD . /app
RUN pip3 install .

ENTRYPOINT ["govee-h5072-logger"]
