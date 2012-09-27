# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Demo car rest client
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
import httplib
import urllib
import sys
if sys.version_info < (3, 0):
  from ConfigParser import ConfigParser
else:
  from configparser import ConfigParser

from commandline import options
from datetime import datetime
from random import *

# config
conf = ConfigParser()
try:
  conf.read(options.pipeconf);
  # pipe settings
  conf.pipeRestUrl = conf.get("pipe", "urlrest")
  conf.host = conf.get("tracker", "host")
except Exception as E:
  log.critical("Error reading " + options.pipeconf + ": " + E.message)
  exit(1)

# logger setup
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr = logging.FileHandler(os.getcwd() + '/send.log')
hdlr.setFormatter(formatter)
logger = logging.getLogger('democlient')
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
logger.debug('START')

# Max sleep time
maxSleep = 600

def sendData(data):
  """
   #Sends data by rest
   #@param data: data string
  """
  logger.debug('REST URL ' + conf.host)
  params = urllib.urlencode(data)
  headers = {
    "Content-type": "application/x-www-form-urlencoded", 
    "Accept": "text/plain"
  }
  conn = httplib.HTTPConnection(conf.host, 80)  
  conn.request("POST", conf.pipeRestUrl, params, headers)
  response = conn.getresponse()

#data for demo cars 
uid1 = "757460032240926_888"
track_files1 = [
  'tracks/car1/1.csv']
uid2 = "857460032240926_888"
track_files2 = [
  'tracks/car2/1.csv']
uid3 = "957460032240926_888"
track_files3 = [
  'tracks/car3/1.csv']
uid4 = "057460032240926_888"
track_files4 = [
  'tracks/car4/1.csv']
uid5 = "157460032240926_888"
track_files5 = [
  'tracks/car5/1.csv']
def movecar(track_files, uid):
  """
   Car moving function - it parse input file and send data to server
   @param track_files: array of file names
   @param uid: device's identifier
   @return: string
  """
  while (True):
    try:
      for track in track_files:
        logger.debug('OPEN: ' + track)
        # Read data from CSV file
        with open(track, 'rb') as f:
          reader = csv.reader(f, delimiter=';', quotechar='"')
          # Prev packet time
          prevTime = 0
          # Last sleep time
          lastSleep = 0
          # Column headers
          h = reader.next();
          for row in reader:
            # Packet time
            curTime = int(datetime.strptime(row[h.index('time')], "%Y-%m-%d %H:%M:%S").strftime("%s"))

            logger.debug('curtime ' + str(curTime))
            logger.debug('Prev time ' + str(prevTime))

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
              #sleep = 10 # temp force sleep time
            # Save prev time
            prevTime = curTime
            logger.debug('Sleep for ' + str(sleep))
            # sleep
            time.sleep(sleep)

            # Sensors
            sensors = {
              'acc': row[h.index('sensor_acc')] if 'sensor_acc' in h else None,
              'odometer': row[h.index('sensor_odometer')]
                if 'sensor_odometer' in h else None,
              'sos': row[h.index('sensor_sos')] if 'sensor_sos' in h else None
            }

            # Data   
            data = {
              'uid': uid, 
              'time': datetime.utcnow(),
              'odometer': row[h.index('sensor_odometer')]
                if 'sensor_odometer' in h else None,
              'lat': row[h.index('latitude')],
              'lon': row[h.index('longitude')],
              'alt': row[h.index('altitude')],
              'speed': row[h.index('speed')],
              'fuel': row[h.index('fuel')],
              'azimuth': row[h.index('azimuth')],
              'movementsensor': row[h.index('movementsensor')],
              'satellitescount': row[h.index('satellitescount')],
              'batterylevel': row[h.index('batterylevel')],
              'hdop': row[h.index('hdop')],
              'sensors': json.dumps(sensors)
            }
            logger.debug('DATA')
            logger.debug(data)

            # Send data by post request
            sendData(data)

        #sleep for 120 seconds and not more than 140 seconds between tracks
        interval = randint(120, 140)
        time.sleep(interval)
    except Exception as E:
      logger.exception(E)
  logger.debug('THREAD EXIT!!!')

threading.Thread(target=movecar, name="thread1", args=[track_files1, uid1]).start()
threading.Thread(target=movecar, name="thread2", args=[track_files2, uid2]).start()
threading.Thread(target=movecar, name="thread3", args=[track_files3, uid3]).start()
threading.Thread(target=movecar, name="thread4", args=[track_files4, uid4]).start()
threading.Thread(target=movecar, name="thread5", args=[track_files5, uid5]).start()
