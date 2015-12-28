#!/usr/bin/env bash
echo 'Starting Galileo default listener'
python3 main.py -c conf/handlers/galileo.default.conf -l conf/logs/galileo.default.conf --pipe_process_mask=$1 -p $2 -s $3
