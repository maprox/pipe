cd ..
echo 'Starting Naviset GT-10 listener'
python3.2 main.py -s conf/handlers/naviset.gt10.conf -l conf/logs/naviset.gt10.conf -p $3 --pipe_server_mask=$1 --port=$2 