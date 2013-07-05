echo 'Starting TR-203 listener'
python3.2 main.py -c conf/handlers/globalsat.tr203.conf -l conf/logs/globalsat.tr203.conf --pipe_process_mask=$1 -p $2 -s $3
