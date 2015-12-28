#!/usr/bin/env bash
echo 'Starting load balancer'
python3 balancer.py -l conf/logs/balancer.conf --pipe_process_mask=$1 -s $3