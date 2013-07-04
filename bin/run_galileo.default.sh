cd ..
echo 'Starting Galileo default listener'
python3.2 main.py -s conf/handlers/galileo.default.conf -l conf/logs/galileo.default.conf -p $3 --pipe_server_mask=$1 --port=$2
