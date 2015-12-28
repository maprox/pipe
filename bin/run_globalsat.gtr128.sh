#!/usr/bin/env bash
echo 'Starting GTR-128/GTR-129 listener'
python3 main.py -c conf/handlers/globalsat.gtr128.conf -l conf/logs/globalsat.gtr128.conf --pipe_process_mask=$1 --port=$2 -s $3
