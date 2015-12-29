#!/usr/bin/env bash

declare -A PIPE_HANDLERS

PIPE_HANDLERS["atrack.ax5"]=21300
PIPE_HANDLERS["autolink.default"]=21301
PIPE_HANDLERS["galileo.default"]=21001
PIPE_HANDLERS["globalsat.gtr128"]=20128
PIPE_HANDLERS["globalsat.tr151"]=20151
PIPE_HANDLERS["globalsat.tr203"]=20203
PIPE_HANDLERS["globalsat.tr206"]=20101
PIPE_HANDLERS["globalsat.tr600"]=20100
PIPE_HANDLERS["globusgps.gltr1mini"]=21010
PIPE_HANDLERS["naviset.gt10"]=21100
PIPE_HANDLERS["naviset.gt20"]=21120
PIPE_HANDLERS["teltonika.fmxxxx"]=21200
PIPE_HANDLERS["teltonika.gh3000"]=21201

for HANDLER_NAME in "${!PIPE_HANDLERS[@]}"; do
    HANDLER_PORT=${PIPE_HANDLERS["$HANDLER_NAME"]}
    echo "Stopping $HANDLER_NAME on port $HANDLER_PORT"

    docker rm -f pipe.$HANDLER_NAME
done

docker rm -f redis
docker rm -f rabbitmq