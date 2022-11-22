#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=bind,src=/var/run/dbus,dst=/var/run/dbus
  --mount type=bind,src=$PWD/flags.txt,dst=/mnt/flags.txt,ro
  --name govee-h5072-logger
  --privileged
  --restart unless-stopped
)

IMAGE=govee-h5072-logger

ARGS=(
  --flagfile=/mnt/flags.txt
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
