cd ..
echo 'Starting Teltonika fmxxxx listener'
python3.2 main.py -s conf/handlers/teltonika.fmxxxx.conf -l conf/logs/teltonika.fmxxxx..conf -p $3 --pipe_server_mask=$1 --port=$2