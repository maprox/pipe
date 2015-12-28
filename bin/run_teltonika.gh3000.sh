#!/usr/bin/env bash
echo 'Starting Teltonika gh3000 listener'
python3 main.py -c conf/handlers/teltonika.gh3000.conf -l conf/logs/teltonika.gh3000.conf --pipe_process_mask=$1 -p $2 -s $3
