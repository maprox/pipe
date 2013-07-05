echo 'Starting TR-206 listener'
python3.2 main.py -c conf/handlers/globalsat.tr206.conf -l conf/logs/globalsat.tr206.conf --pipe_process_mask=$1 -p $2 -s $3
