cd ..
echo 'Starting GTR-128/GTR-129 listener'
python3.2 main.py -s conf/handlers/globalsat.gtr128.conf -l conf/logs/globalsat.gtr128.conf -p $3 --pipe_server_mask=$1 --port=$2
