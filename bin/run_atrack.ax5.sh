echo 'Starting ATrack listener'
python3 main.py -c conf/handlers/atrack.ax5.conf -l conf/logs/atrack.ax5.conf --pipe_process_mask=$1 --port=$2 -s $3
