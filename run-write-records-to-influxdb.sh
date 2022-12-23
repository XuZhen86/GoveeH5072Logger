#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=volume,src=govee-h5072-logger-data,dst=/app/data
  --mount type=volume,src=govee-h5072-logger-profile,dst=/app/profile
  --name govee-h5072-logger-write-records-to-influxdb
  --restart unless-stopped
)

IMAGE=govee-h5072-logger

ARGS=(
  govee-h5072-logger-write-records-to-influxdb
  --flagfile=data/write-records-to-influxdb-flags.txt
  --verbosity=0
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
