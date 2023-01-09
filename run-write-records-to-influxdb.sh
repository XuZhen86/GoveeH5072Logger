#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=volume,src=govee-h5072-logger-data,dst=/app/data
  --name govee-h5072-logger-write-records-to-influxdb
  --restart unless-stopped
)

IMAGE=line-protocol-cache-consumer

ARGS=(
  line-protocol-cache-consumer
  --flagfile=data/line-protocol-cache-consumer-flags.txt
  --verbosity=0
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
