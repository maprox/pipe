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
import os
import csv
import httplib
import urllib
####
import sys
if sys.version_info < (3, 0):
  from ConfigParser import ConfigParser
else:
  from configparser import ConfigParser

from commandline import options
####
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
  logger.debug(response.status)

#data for demo cars 
uid1 = "457460032240926_888"
track_files1 = [
  'tracks/car1/1.csv']
uid2 = "557460032240926_888"
track_files2 = [
  'tracks/car2/1.txt',
  'tracks/car2/2.txt',
  'tracks/car2/3.txt',
  'tracks/car2/4.txt',
  'tracks/car2/5.txt',
  'tracks/car2/6.txt']
uid3 = "657460032240926_888"
track_files3 = [
  'tracks/car3/1.txt',
  'tracks/car3/2.txt',
  'tracks/car3/3.txt',
  'tracks/car3/4.txt',
  'tracks/car3/5.txt',
  'tracks/car3/6.txt']

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
          # Column headers
          h = reader.next();
          for row in reader:
            logger.debug('sc ' + row[h.index('satellitescount')])
            # Data   
            data = {
              'uid': uid, 
              'time': datetime.utcnow(),
              #'odometer': row[h.index('odometer')]
              'lat': row[h.index('latitude')],
              'lon': row[h.index('longitude')],
              'alt': row[h.index('altitude')],
              'speed': row[h.index('speed')],
              'azimuth': row[h.index('azimuth')],
              'movementsensor': row[h.index('movementsensor')],
              'satellitescount': row[h.index('satellitescount')],
              'batterylevel': row[h.index('batterylevel')],
              'hdop': row[h.index('hdop')]
            }
            # Send data by post request
            sendData(data)

            # Random sleep
            sleep = randint(10, 20)
            time.sleep(sleep)
        #sleep for 2 hours and not more than 20 minutes between tracks
        interval = randint(120, 140)
        time.sleep(interval)
    except Exception as E:
      logger.exception(E)
  logger.debug('THREAD EXIT!!!')

threading.Thread(target=movecar, name="thread1", args=[track_files1, uid1]).start()
#threading.Thread(target=movecar, name="thread2", args=[track_files2, uid2]).start()
#threading.Thread(target=movecar, name="thread3", args=[track_files3, uid3]).start()
#threading.Thread(target=movecar, name="thread4", args=[track_files4, uid4]).start()
