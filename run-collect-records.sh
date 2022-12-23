#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=bind,src=/var/run/dbus,dst=/var/run/dbus
  --mount type=volume,src=govee-h5072-logger-data,dst=/app/data
  --mount type=volume,src=govee-h5072-logger-profile,dst=/app/profile
  --name govee-h5072-logger-collect-records
  --privileged
  --restart unless-stopped
)

IMAGE=govee-h5072-logger

ARGS=(
  govee-h5072-logger-collect-records
  --flagfile=data/collect-records-flags.txt
  --verbosity=0
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
