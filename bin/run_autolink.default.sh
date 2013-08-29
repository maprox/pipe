echo 'Starting Autolink Default listener'
python3 main.py -c conf/handlers/autolink.default.conf -l conf/logs/autolink.default.conf --pipe_process_mask=$1 -p $2 -s $3
