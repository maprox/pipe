echo 'Starting ATrack listener'
python3.2 main.py -c conf/handlers/atrack.ax5.conf -l conf/logs/atrack.ax5.conf --pipe_server_mask=$1 --port=$2 -s $3
