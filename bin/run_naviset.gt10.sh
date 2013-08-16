echo 'Starting Naviset GT-10 listener'
python3 main.py -c conf/handlers/naviset.gt10.conf -l conf/logs/naviset.gt10.conf --pipe_process_mask=$1 -p $2 -s $3
