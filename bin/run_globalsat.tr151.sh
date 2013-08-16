echo 'Starting TR-151 listener'
python3 main.py -c conf/handlers/globalsat.tr151.conf -l conf/logs/globalsat.tr151.conf --pipe_process_mask=$1 -p $2 -s $3
