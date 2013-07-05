echo 'Starting Teltonika fmxxxx listener'
python3.2 main.py -c conf/handlers/teltonika.fmxxxx.conf -l conf/logs/teltonika.fmxxxx..conf --pipe_server_mask=$1 -p $2 -s $3
