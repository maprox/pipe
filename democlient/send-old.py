# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Demo car client
@copyright 2009-2012, Maprox LLC
'''

import re
import socket
import codecs
import time
import threading
import logging
import os
from datetime import datetime
from random import *

# logger setup
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr = logging.FileHandler(os.getcwd() + '/send.log')
hdlr.setFormatter(formatter)
logger = logging.getLogger('democlient')
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
logger.debug('START')

# regexp config
rc_lat = '^(N\d+ \d+.\d+)'
rc_lon = '(E(\d+) (\d+.\d+))$'
rc_packet = '^Trackpoint'
rc_int = '^(\d+)'
rc_odometer = '^(\d+[.]{0,1}[\d+]{0,5}) (.+)'
rc_hdop = '([\d]+(?:\.\d)?)'
value_sep = '	'

re_packet = re.compile(rc_packet)
re_lat = re.compile(rc_lat)
re_lon = re.compile(rc_lon)
re_int = re.compile(rc_int)
re_odometer = re.compile(rc_odometer)
re_hdop = re.compile(rc_hdop)

host, port = "localhost", 20100

def getLat(s):
    """
     Parsing latitude value
     @param data: data string
     @return: string
    """
    g = re_lat.search(s).group(1)
    return g.replace(' ', '') + '0'

def getLon(s):
    """
     Parsing longitude value
     @param data: data string
     @return: string
    """
    g = re_lon.search(s).groups()
    part1 = g[1]
    while (len(part1) < 3):
      part1 = '0' + part1
    return 'E' + part1 + g[2] + '0'

def getInt(s):
    """
     Parsing int value
     @param data: data string
     @return: string
    """
    s = s.replace('-', '')
    return re_int.search(s).group(1)

def getOdometer(s):
    """
     Parsing odometer value
     @param data: data string
     @return: string
    """
    g = re_odometer.search(s).groups()
    val = float(g[0])
    if (g[1] == 'km'):
      val = val * 1000
    return str(int(round(val)))

def getHdop(s):
    """
     Parsing odometer value
     @param data: data string
     @return: string
    """
    g = re_hdop.search(s).groups()
    val = float(g[0])
    return str(round(val, 1))

def getChecksum(data):
    """
     Returns the data checksum
     @param data: data string
     @return: hex string checksum
    """
    csum = 0
    for c in data:
        csum ^= ord(c)
    hex_csum = "%02X" % csum
    return hex_csum

def sendData(data):
    """
     Sends data to python server in Globalsat TR-600 format
     @param data: data string
    """
    try:
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        #d = bytes(data + "\r\n", "ascii")
        d = bytes(data + "\r\n")
        #print(data)
        sock.send(d)
        sock.close()
    except Exception as E:
        logger.exception(E)

#data for demo cars
template_str1 = "GSr,457460032240926_888,00,5,e080,e080,3,"
track_files1 = [
  'tracks/car1/1.txt',
  'tracks/car1/2.txt']
template_str2 = "GSr,557460032240926_888,00,5,e080,e080,3,"
track_files2 = [
  'tracks/car2/1.txt',
  'tracks/car2/2.txt',
  'tracks/car2/3.txt',
  'tracks/car2/4.txt',
  'tracks/car2/5.txt',
  'tracks/car2/6.txt']
template_str3 = "GSr,657460032240926_888,00,5,e080,e080,3,"
track_files3 = [
  'tracks/car3/1.txt',
  'tracks/car3/2.txt',
  'tracks/car3/3.txt',
  'tracks/car3/4.txt',
  'tracks/car3/5.txt',
  'tracks/car3/6.txt']
template_str4 = "GSr,757460032240926_888,00,5,e080,e080,3,"
track_files4 = [
  'tracks/car4/1.txt',
  'tracks/car4/2.txt']

def movecar(track_files, template_str):
    """
     Car moving function - it parse input file and send data string to server
     @param track_files: array of file names
     @param template_str: string data string template
     @return: string
    """
    while (True):
        try:
            for track in track_files:
                logger.debug('OPEN: ' + track)
                f = codecs.open(track, 'r', 'utf-8')
                for line in f.xreadlines():
                    m = re_packet.match(line)
                    if (m):
                        s_parts = line.split(value_sep)
                        if (len(s_parts) >= 10):
                            # get data from file
                            lat = getLat(s_parts[1])
                            lon = getLon(s_parts[1])
                            speed = str(int(getInt(s_parts[8])) / 1.852)
                            altitude = getInt(s_parts[3])
                            azimuth = getInt(s_parts[9])
                            odometer = getOdometer(s_parts[6])
                            if (len(s_parts) >= 11):
                              sat_count = getInt(s_parts[10])
                            else:
                              sat_count = str(randint(8, 12))
                            if (len(s_parts) >= 12):
                              hdop = getHdop(s_parts[11])
                            else:
                              hdop = '1.0'
                            # random get other data

                            # create result string
                            now = datetime.utcnow()
                            res_str = template_str + now.strftime('%d%m%y') + ','
                            res_str = res_str + now.strftime('%H%M%S') + ','
                            res_str = res_str + lon + ',' + lat + ',' + altitude + ',' + speed + ','
                            res_str = res_str + azimuth + ',' + sat_count + ','
                            res_str = res_str + hdop + ','
                            res_str = res_str + '14600,14470mV,0,0,0,0,0,' + odometer + ',0'
                            #add the checksum
                            checksum = getChecksum(res_str)              
                            res_str = res_str + '*' + checksum + '!'
                            logger.debug('ORIGRESTR ' + res_str)
                            sendData(res_str)

                            #random sleep
                            sleep = randint(10, 20)
                            time.sleep(sleep)
                f.close()
                #sleep for 2 hours and not more than 20 minutes between tracks
                interval = randint(120, 140)
                time.sleep(interval)
        except Exception as E:
            logger.exception(E)

threading.Thread(target=movecar, name="thread1", args=[track_files1, template_str1]).start()
threading.Thread(target=movecar, name="thread2", args=[track_files2, template_str2]).start()
threading.Thread(target=movecar, name="thread3", args=[track_files3, template_str3]).start()
#threading.Thread(target=movecar, name="thread4", args=[track_files4, template_str4]).start()
