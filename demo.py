# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Demo cars client
@copyright 2009-2013, Maprox LLC
'''

import time
import threading
import json
import os
import glob
import csv

from random import *
from datetime import datetime
from kernel.logger import log
from lib.broker import broker

fmtDate = "%Y-%m-%d %H:%M:%S"
maxSleep = 600
maxParkingTime = 600
minParkingSpeed = 1

def sendData(data):
    """
     Sends packets to the RabbitMQ
     @param data: dict
    """
    broker.send([data])

def movecar(packet):
    """
     Car moving function - it parse input file and send data to server
     @param packet: dict
     @return: string
    """
    while (True):
        try:
            for track in packet['track_files']:
                log.debug('OPEN: ' + track)
                # Read data from CSV file
                prevTime = 0 # Prev packet time
                lastSleep = 0 # Last sleep time
                parkingStartTime = 0 # Parking start time
                # Column headers
                reader = csv.DictReader(
                  open(track, newline='', encoding='utf-8'),
                  dialect="excel",
                  delimiter=';'
                )
                for row in reader:
                    #log.debug(row)
                    packetTime = row['time']
                    #log.debug('time = %s', packetTime)
                    dt = datetime.strptime(packetTime, fmtDate)
                    curTime = time.mktime(dt.timetuple())

                    #log.debug('Cur time ' + str(curTime))
                    #log.debug('Prev time ' + str(prevTime))

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

                    #log.debug('speed ' + row['speed'] + ' state ' + row['state'])

                    # Check if parking begin
                    if (float(row['speed']) <= minParkingSpeed or \
                            int(row['state']) == 4):
                        # Save parking start time
                        if (parkingStartTime == 0):
                            parkingStartTime = curTime
                            #log.debug('Set parking start time to cur')

                        if ((curTime - parkingStartTime) + sleep >= maxParkingTime):
                            #sleep = 0;
                            #log.debug('>>>Set sleep to 0 (continue)')
                            continue

                        #log.debug('normal sleep')
                    # Check if moving begin
                    if (float(row['speed']) > minParkingSpeed \
                            and int(row['state']) != 4):
                        #log.debug('Reset parking start time')
                        parkingStartTime = 0

                    #log.debug('Sleep for ' + str(sleep))
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
                        'uid': packet['uid'],
                        'time': datetime.utcnow().strftime(fmtDate),
                        'sensors': sensors,
                        # all of the fields above must be in sensors
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'altitude': row['altitude'],
                        'speed': row['speed'],
                        'azimuth': row['azimuth'],
                        'satellitescount': row['satellitescount'],
                        'hdop': row['hdop']
                    }

                    # Send data by post request
                    sendData(data)

                # Sleep for 120-140 seconds between tracks
                interval = randint(120, 140)
                time.sleep(interval)
        except Exception as E:
            log.exception(E)

from configparser import ConfigParser
from optparse import OptionParser
options = OptionParser()
options.add_option(
    "-d",
    "--dir",
    dest="dir",
    help="Demo tracks directory",
    metavar="TracksDirectory",
    default="demo/tracks"
)
(options, args) = options.parse_args()

data = []
os.chdir(options.dir)
for files in glob.glob("*.conf"):
    carconf = ConfigParser()
    try:
        carconf.read(files)
        data.append({
            'uid': carconf.get("car", "uid"),
            'track_files': [files.replace('.conf', '.csv')]
        })
    except Exception as E:
        log.warn("Error preparing " + options.dir + "/" + files)

for i, t in enumerate(data):
    threading.Thread(
        target = movecar,
        name = "t" + str(i),
        args = [t]
    ).start()
