echo 'Starting GlobusGps GL-TR1-mini listener'
python3 main.py -c conf/handlers/globusgps.gltr1mini.conf -l conf/logs/globusgps.gltr1mini.conf --pipe_process_mask=$1 -p $2 -s $3
