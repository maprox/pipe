# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Demo car rest client
@copyright 2009-2012, Maprox LLC
'''

import re
import socket
import codecs
import time
import threading
import logging
import logging.handlers
import json
import os
import glob
import csv
import http.client
import urllib.parse
import sys
if sys.version_info < (3, 0):
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

from commandline import options
from random import *

# logger setup
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr = logging.handlers.RotatingFileHandler(os.getcwd() + '/send.log', 'a', \
	5 * 1024 * 1024, 5)
hdlr.setFormatter(formatter)
logger = logging.getLogger('democlient')
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
logger.debug('START!')

# config
conf = ConfigParser()
try:
    conf.read(options.pipeconf);
    # pipe settings
    conf.pipeRestUrl = conf.get("pipe", "urlrest")
    urlParts = re.search('//(.+?)(/.+)', conf.pipeRestUrl)
    conf.restHost = urlParts.group(1)
    conf.restPath = urlParts.group(2)
    conf.host = conf.get("tracker", "host")
except Exception as E:
    logger.critical("Error reading " + options.pipeconf + ": " + E.message)
    exit(1)

# Max sleep time
if options.dir != 'navitech':
    maxSleep = 600
else:
    maxSleep = 60
    
# Max parking time
maxParkingTime = 600

# Min parking speed
minParkingSpeed = 1

def sendData(data):
    """
     #Sends data by rest
     #@param data: data string
    """
    params = urllib.parse.urlencode(data)
    headers = {
      "Content-type": "application/x-www-form-urlencoded", 
      "Accept": "text/plain"
    }
    conn = http.client.HTTPConnection(conf.restHost, 80)  
    conn.request("POST", conf.restPath, params, headers)
    response = conn.getresponse()

def movecar(packet):
    """
     Car moving function - it parse input file and send data to server
     @param packet: dict
     @return: string
    """

    from datetime import datetime

    while (True):
        try:
            for track in packet['track_files']:
                logger.debug('OPEN: ' + track)
                # Read data from CSV file
                # Prev packet time
                prevTime = 0
                # Last sleep time
                lastSleep = 0
                # Parking start time
                parkingStartTime = 0
                # Column headers
                reader = csv.DictReader(
                  open(track, newline='', encoding='utf-8'),
                  dialect="excel",
                  delimiter=';'
                )
                for row in reader:
                    dt = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    curTime = time.mktime(dt.timetuple())

                    #logger.debug('Cur time ' + str(curTime))
                    #logger.debug('Prev time ' + str(prevTime))

                    # If first packet, send it now
                    if (prevTime == 0):
                        sleep = 0
                    else:
                        # Count sleep time
                        sleep = curTime - prevTime
                        # Sleeping time can not be more than maxSleep
                        if (sleep > maxSleep):
                            # Check pervious sleep time
                            if (lastSleep >= maxSleep):
                                lastSleep = sleep
                                sleep = 0
                            else:
                                sleep = maxSleep
                                lastSleep = sleep
                        else:
                          lastSleep = sleep

                    # Save prev time
                    prevTime = curTime

                    #logger.debug('speed ' + row['speed'] + ' state ' + row['state'])

                    # Check if parking begin
                    if (float(row['speed']) <= minParkingSpeed or int(row['state']) == 4):
                        # Save parking start time
                        if (parkingStartTime == 0):
                            parkingStartTime = curTime
                            #logger.debug('Set parking start time to cur')

                        if ((curTime - parkingStartTime) + sleep >= maxParkingTime):
                            #sleep = 0;
                            #logger.debug('>>>Set sleep to 0 (continue)')
                            continue

                        #logger.debug('normal sleep')
                    # Check if moving begin
                    if (float(row['speed']) > minParkingSpeed and int(row['state']) != 4):
                        #logger.debug('Reset parking start time')
                        parkingStartTime = 0;

                    #logger.debug('Sleep for ' + str(sleep))
                    # sleep
                    time.sleep(sleep)

                    # Sensors
                    sensors = {
                      'acc': row['sensor_acc'] \
                          if 'sensor_acc' in row else None,
                      'sos': row['sensor_sos'] \
                          if 'sensor_sos' in row else None,
                      'ext_battery_level': row['sensor_ext_battery_level'] \
                          if 'sensor_ext_battery_level' in row else None,
                      'ain0': row['ain0'] \
                          if 'ain0' in row else None,
                      'latitude': row['latitude'],
                      'longitude': row['longitude'],
                      'altitude': row['altitude'],
                      'speed': row['speed'],
                      'azimuth': row['azimuth'],
                      'sat_count': row['satellitescount'],
                      'hdop': row['hdop']
                    }

                    odometer = row['sensor_odometer'] \
                      if 'sensor_odometer' in row else None

                    if (odometer):
                        sensors['odometer'] = odometer

                    # Data
                    data = {
                        'device_key': packet['device_key'],
                        'uid': packet['uid'],
                        'time': datetime.utcnow(),
                        'odometer': row['sensor_odometer']
                          if 'sensor_odometer' in row else None,
                        'sensors': json.dumps(sensors)
                    }

                    # Send data by post request
                    sendData(data)

                # Sleep for 120-140 seconds between tracks
                interval = randint(120, 140)
                time.sleep(interval)
        except Exception as E:
            logger.exception(E)

data = []

os.chdir(options.dir)
for files in glob.glob("*.conf"):
	carconf = ConfigParser()
	try:
		carconf.read(files);
		data.append({
			'device_key': carconf.get("car", "key"),
			'uid': carconf.get("car", "uid"),
			'track_files': [files.replace('.conf', '.csv')]
		})
	except Exception as E:
		logger.warn("Error preparing " + options.dir + "/" + files)

for i, t in enumerate(data):
    threading.Thread(target=movecar, name="t" + str(i), args=[t]).start()
