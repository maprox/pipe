cd ..
echo 'Starting Naviset GT-20 listener'
python3.2 main.py -s conf/handlers/naviset.gt20.conf -l conf/logs/naviset.gt20.conf -p $3 --pipe_server_mask=$1 --port=$2
