cd ..
echo 'Starting TR-203 listener'
python3.2 main.py -s conf/handlers/globalsat.tr203.conf -l conf/logs/globalsat.tr203.conf -p $3 --pipe_server_mask=$1 --port=$2
