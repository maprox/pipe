echo 'Starting TR-600 listener'
python3 main.py -c conf/handlers/globalsat.tr600.conf -l conf/logs/globalsat.tr600.conf --pipe_process_mask=$1 -p $2 -s $3
