cd ..
echo 'Starting TR-206 listener'
python3.2 main.py -s conf/handlers/globalsat.tr206.conf -l conf/logs/globalsat.tr206.conf -p $3 --pipe_server_mask=$1 --port=$2