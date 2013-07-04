cd ..
echo 'Starting TR-151 listener'
python3.2 main.py -s conf/handlers/globalsat.tr151.conf -l conf/logs/globalsat.tr151.conf -p $3 --pipe_server_mask=$1 --port=$2
