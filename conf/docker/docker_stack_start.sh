#!/usr/bin/env bash

PIPE_ENVIRONMENT="production"
PIPE_HOSTNAME="trx.maprox.net"
PIPE_HOSTIP="212.100.159.142"
REDIS_PASS="x71cjhniooVm4ouv5eK1"
RABBITMQ_PASS="oi4eI3s4euouACEQiV8E"

docker run -d --name redis \
  -e REDIS_PASS=$REDIS_PASS \
  tutum/redis

docker run -d --name rabbitmq \
  -e RABBITMQ_PASS=$RABBITMQ_PASS \
  tutum/rabbitmq

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
    echo "$HANDLER_NAME has port $HANDLER_PORT"

    docker run -d --name pipe.$HANDLER_NAME \
        -e PIPE_ENVIRONMENT=$PIPE_ENVIRONMENT \
        -e PIPE_HOSTNAME=$PIPE_HOSTNAME \
        -e PIPE_HOSTIP=$PIPE_HOSTIP \
        -e PIPE_HANDLER=$HANDLER_NAME \
        -e PIPE_PORT=$HANDLER_PORT \
        -e REDIS_HOST=redis \
        -e REDIS_PASS=$REDIS_PASS \
        -e AMQP_CONNECTION="amqp://admin:$RABBITMQ_PASS@rabbitmq//" \
        --link redis \
        --link rabbitmq \
        -p $HANDLER_PORT:$HANDLER_PORT \
        maprox/pipe

done