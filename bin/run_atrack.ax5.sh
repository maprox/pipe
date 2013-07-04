cd ..
echo 'Starting ATrack listener'
python3.2 main.py -s conf/handlers/atrack.ax5.conf -l conf/logs/atrack.ax5.conf -p $3 --pipe_server_mask=$1 --port=$2