cd ..
echo 'Starting TR-600 listener'
python3.2 main.py -s conf/handlers/globalsat.tr600.conf -l conf/logs/globalsat.tr600.conf -p $3 --pipe_server_mask=$1 --port=$2
