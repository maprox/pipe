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
import json
import os
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
hdlr = logging.FileHandler(os.getcwd() + '/send.log')
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
maxSleep = 600

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
                        # Sleeping time can not be more than 20 minutes
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
                    #logger.debug('Sleep for ' + str(sleep))
                    # sleep
                    time.sleep(sleep)

                    # Sensors
                    sensors = {
                      'acc': row['sensor_acc'] \
                          if 'sensor_acc' in row else None,
                      'sos': row['sensor_sos'] \
                          if 'sensor_sos' in row else None,
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
                        'lat': row['latitude'],
                        'lon': row['longitude'],
                        'alt': row['altitude'],
                        'speed': row['speed'],
                        'fuel': row['fuel'],
                        'azimuth': row['azimuth'],
                        'movementsensor': row['movementsensor'],
                        'satellitescount': row['satellitescount'],
                        'batterylevel': row['batterylevel'],
                        'hdop': row['hdop'],
                        'sensors': json.dumps(sensors)
                    }

                    # Send data by post request
                    sendData(data)

                # Sleep for 120-140 seconds between tracks
                interval = randint(120, 140)
                time.sleep(interval)
        except Exception as E:
            logger.exception(E)

data = [{
  "device_key": "a9265e4b14c08a491c85723ec7af6329",
  "uid": "757460032240926_888",
  "track_files": ['tracks/car1/1.csv']
}, {
  "device_key": "075be5b737d7ad9a7f109aa7bdd32f15",
  "uid": "857460032240926_888",
  "track_files": ['tracks/car2/1.csv']
}, {
  "device_key": "0b1c0b070bf53c6a9f0dfac9308498f2",
  "uid": "957460032240926_888",
  "track_files": ['tracks/car3/1.csv']
}, {
  "device_key": "39561823c27a6a891de8e078fa02a69f",
  "uid": "057460032240926_888",
  "track_files": ['tracks/car4/1.csv']
}, {
  "device_key": "991996e1ee344dd3a49a99cf7089d023",
  "uid": "157460032240926_888",
  "track_files": ['tracks/car5/1.csv']
}]

for i, t in enumerate(data):
    threading.Thread(target=movecar, name="t" + str(i), args=[t]).start()