# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globalsat base class for other Globalsat protocols
@copyright 2009-2013, Maprox LLC
"""

import re
import json
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from kernel.dbmanager import db
from lib.handler import AbstractHandler
from lib.geo import Geo

from lib.handlers.globalsat.commands import CommandFactory
from lib.handlers.globalsat.packets import *

class GlobalsatHandler(AbstractHandler):
    """
     Base handler for Globalsat protocol
    """

    reportFormat = "SPRXYAB27GHKLMmnaefghio*U!"

    re_patterns = {
      'line': '(?P<line>(?P<head>GS\w){fields})\*(?P<checksum>\w+)!',
      'field': ',(?P<{field}>{value})',
      'unknownField': '[\w\.]*',
      'service': {
        'I': '\w+',
        'T': '[0-3]',
        'S': '[1-9]?\d'
      },
      'report': {
        'A': '[1-3]',
        'B': '\d{6},\d{6}',
        'C': '\d{6},\d{6}',
        '1': '[EW]\d{3}\.\d{6}',
        '2': '[EW]\d{5}\.\d{4}',
        '3': '[+-]\d{9}',
        '6': '[NS]\d{2}\.\d{6}',
        '7': '[NS]\d{4}\.\d{4}',
        '8': '[+-]\d{8}',
        'G': '\d+',
        'H': '\d+(\.\d+)?',
       #'I': '',
       #'J': '',
        'K': '\d+',
        'L': '\d+',
        'M': '\d+(\.\d+)?',
        'N': '\d+',
        'P': '[0-9A-F]{2,}',
       #'Z': '',
       #'Q': '',
        'R': '\w',
        'S': '\w+',
        'T': '\w+',
       #'U': '',
        'V': '[0-9A-F]{2,}',
        'W': '[0-9A-F]{2,}',
        'X': '[\w\.]+',
        'Y': '\w{4}',
        'a': '\d+',
        'e': '\d+',
        'f': '\d+',
        'g': '\d+',
        'h': '\d+',
        'i': '\d+',
        'm': '\d+',
        'n': '(\w+|\d+%)',
        'o': '\d+'
       #'s': ''
      },
      'search_config': 'GSs,(?P<uid>\w+),(?P<status>\d+),(?P<order>\d+),(?P<data>.*)\*[a-f\d]{1,2}\!',
      'search_uid': 'GS\w,(?P<uid>\w+)'
    }

    re_compiled = {
      'service': None,
      'report': None,
      'search_uid': None,
      'search_config': None
    }

    re_volts = re.compile('(\d+)mV')
    re_percents = re.compile('(\d+)%')
    re_number = re.compile('(\d+)')

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        super(GlobalsatHandler, self).initialization()
        self._commandsFactory = CommandFactory()
        self.reportFormat = truncateChecksum(
            conf.get('settings', "reportFormat"))
        self.__compileRegularExpressions()

    def __compileRegularExpressions(self):
        """
         Compiling of regular expressions
        """
        # Let's start with report format
        p = self.re_patterns
        fieldsStr = ""
        for char in self.reportFormat:
            pattern = p['unknownField']
            if char in p['report']:
                pattern = p['report'][char]
            # We need to avoid digital names of groups
            fieldName = char
            if char.isdigit():
                fieldName = "d" + char
            fieldsStr += str.format(p['field'],
              field = fieldName, value = pattern)
        line = str.format(p['line'], fields = fieldsStr)
        self.re_compiled['report'] = re.compile(line, flags = re.IGNORECASE)
        # Compiling the pattern for uid searching
        self.re_compiled['search_uid'] = \
          re.compile(p['search_uid'], flags = re.IGNORECASE)
        self.re_compiled['search_config'] = re.compile(p['search_config'])
        return self

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        packet = {}
        sensor = {}
        for char in data:
            value = data[char]
            if value == '': value = '0'
            # IMEI / UID
            if char == "S":
                packet['uid'] = value
            # TIME
            elif char == "B":
                dt = datetime.strptime(value, '%d%m%y,%H%M%S')
                packet['time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
            # COORD
            elif char in ("d1", "d2", "d3"):
                packet['longitude'] = Geo.getLongitude(value)
            elif char in ("d6", "d7", "d8"):
                packet['latitude'] = Geo.getLatitude(value)
            # ALTITUDE
            elif char == "G":
                packet['altitude'] = int(round(float(value)))
            # SPEED (knots)
            elif char == "H":
                packet['speed'] = 1.852 * float(value)
            # SPEED (km/hr)
            elif char == "I":
                packet['speed'] = value
            # SPEED (mile/hr)
            elif char == "J":
                packet['speed'] = 1.609344 * float(value)
            # Satellites count
            elif char == "L":
                packet['satellitescount'] = int(value)
                sensor['sat_count'] = int(value)
            # Azimuth - driving direction
            elif char == "K":
                packet['azimuth'] = int(round(float(value)))
            # Odometer
            elif char == "i":
                sensor['odometer'] = float(value)
            # HDOP (Horizontal Dilution of Precision)
            elif char == "M":
                packet['hdop'] = float(value)
            # Extracting movement sensor from report type.
            # Have lower priority than actual movement sensor
            elif char == "R":
                if not 'moving' in sensor:
                    sensor['moving'] = int(value != '4' and
                      value != 'F' and
                      value != 'E')
            # Extracting movement sensor value and ACC
            elif char == "Y":
                # Tracker sends value as HEX string
                dec = int(value, 16)
                # Digital inputs
                sensor['din1'] = (dec >> 1) % 2
                sensor['din2'] = (dec >> 2) % 2
                sensor['din3'] = (dec >> 3) % 2
                # Movement sensor
                sensor['moving'] = (dec >> 7) % 2
                # Digital outputs
                sensor['dout1'] = (dec >> 9) % 2
                sensor['dout2'] = (dec >> 10) % 2
                sensor['dout3'] = (dec >> 11) % 2
                # ACC Sensor
                sensor['acc'] = (dec >> 13) % 2
                # GPS Antenna
                sensor['sat_antenna_connected'] = (dec >> 14) % 2
                # No external power
                sensor['ext_battery_connected'] = (dec >> 15) % 2
            # Signalization status
            elif char == "P":
                dec = int(value, 16)
                sensor['sos'] = dec % 2
            # Counters
            elif char == "e":
                sensor['counter0'] = float(value)
            elif char == "f":
                sensor['counter1'] = float(value)
            elif char == "g":
                sensor['counter2'] = float(value)
            elif char == "h":
                sensor['counter3'] = float(value)
            # Analog input 0
            elif char == "a":
                sensor['ain0'] = float(value)
            elif char == "m":
                sensor['ext_battery_voltage'] = float(value)
        self.setPacketSensors(packet, sensor)
        return packet

    def formatExtBatteryVoltage(self, value):
        """
         Get external battery voltage
         @param value: string data from gps-tracker
        """
        if self.re_volts.match(value):
            return float(self.re_volts.search(value).group(1))
        else:
            return 0

    def formatBatteryLevel(self, value):
        """
         Formats batterylevel into float
         @param value: string data from gps-tracker
        """
        if self.re_percents.match(value):
            return float(self.re_percents.search(value).group(1))
        elif self.re_volts.match(value) or self.re_number.match(value):
            return 100
        else:
            return 0

    def translateConfig(self, data):
        """
         Translate gps-tracker config data to observer format
         @param data: {string[]} data from gps-tracker
        """
        send = {}
        send['raw'] = data

        tmp_options = send['raw'].split(',')
        options = {}
        for option in tmp_options:
            option = option.split('=')
            key = option[:1][0]
            del option[:1]
            value = '='.join(option)
            options[key] = value

        return self.translateConfigOptions(send, options)

    def translateConfigOptions(self, send, options):
        """
         Translate gps-tracker parsed options to observer format
         @param send: {string[]} data to send
         @param options: {string[]} parsed options
        """
        if 'O5' in options:
            send['identifier'] = options['O5']
        if 'O7' in options:
            send['version'] = options['O7']
        if 'G0' in options:
            send['sos_phone_1'] = options['G0']
        if 'G1' in options:
            send['sos_phone_2'] = options['G1']
        if 'G2' in options:
            send['sos_phone_3'] = options['G2']
        if 'G3' in options:
            send['sos_phone_4'] = options['G3']
        if 'G4' in options:
            send['sos_phone_5'] = options['G4']
        if 'G5' in options:
            send['sos_phone_6'] = options['G5']
        send['identifier'] = self.uid

        return send

    def getFunction(self, data):
        """
         Returns a function name according to supplied data
         @param data: data string
         @return: function name
        """
        data_type = data.split(",")[0]
        if data_type == 'GSs':
            return "processSettings"
        elif data_type == 'GSr' or data_type == 'GSb':
            return "processData"
        else:
            raise NotImplementedError("Unknown data type " + data_type)

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
        """
        initialData = data

        # let's work with text data
        data = data.decode()

        function_name = self.getFunction(data)
        if function_name != 'processData':
            function = getattr(self, function_name)
            return function(data)

        rc = self.re_compiled['report']
        position = 0

        log.debug("Data received:\n%s", data)
        m = rc.search(data, position)
        if not m:
            self.processError(data)

        while m:
            # - OK. we found it, let's see for checksum
            log.debug("Raw match found.")
            data_device = m.groupdict()
            cs1 = str.upper(data_device['checksum'])
            cs2 = str.upper(getChecksum(data_device['line']))
            if cs1 == cs2:
                packetObserver = self.translate(data_device)
                log.info(packetObserver)
                self.uid = packetObserver['uid']
                self._buffer = m.group(0).encode()
                self.store([packetObserver])
                if packetObserver['sensors']['sos'] == 1:
                    self.stopSosSignal()
            else:
                log.error("Incorrect checksum: %s against computed %s",
                  cs1, cs2)
            position += len(m.group(0))
            m = rc.search(data, position)

        return super(GlobalsatHandler, self).processData(initialData)

    def sendInternalCommand(self, commandText):
        """
         Send command
        """
        command = 'GSC,' + self.uid + ',' + commandText
        command = addChecksum(command)
        log.debug('Command sent: ' + command)
        self.send(command.encode())
        return self

    def stopSosSignal(self):
        """
         Send command to stop sos signal
        """
        return self.sendInternalCommand('Na')

    def processSettings(self, data):
        """
         Reading of device settings
         @param data: data string with device settings
         @return: self
        """
        rc = self.re_compiled['search_config']
        position = 0
        m = rc.search(data, position)

        if not m:
            self.processError(data)

        while m:
            log.debug("Config match found.")
            data_settings = m.groupdict()
            self.saveSettings(data_settings)
            position += len(m.group(0))
            m = rc.search(data, position)

        return self

    def saveSettings(self, data):
        """
         Save device setting
         @param data: device setting
        """
        current_db = db.get(data['uid'])
        current_db.addSettings(data['data'] + ',')
        log.debug('Transmission status: ' + data['status'])
        if data['status'] == '2':
            current_db.finishSettingsRead()

    def processError(self, data):
        """
         OK. Our pattern doesn't match the socket or config data.
         The source of the problem can be in wrong report format.
         Let's try to find UID of device.
         Later it would be good to load particular
         config for device by its uid
        """
        rc = self.re_compiled['search_uid']
        mu = rc.search(data)
        if not mu:
            log.error("Unknown data format...")
        else:
            log.error("Unknown data format for %s", mu.group('uid'))

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        current_db = db.get(self.uid)
        if not current_db.isReadingSettings() \
          and not current_db.isSettingsReady():
            current_db.startReadingSettings(task)
            self.sendInternalCommand('N1(OO=02),L1(ALL)')
        self.processCloseTask(task, None)

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        current_db = db.get(self.uid)
        if not current_db.isReadingSettings():
            command = 'GSS,' + self.uid + ',3,0'
            data = json.loads(data)
            if type(data) is dict:
                data = [data]
            command = command + self.addCommandSetOptions(data)
            command = addChecksum(command)
            log.debug('Command sent: ' + command)
            self.send(command.encode())
            self.processCommandReadSettings(task, None)
            self.processCloseTask(task, None)

    def addCommandSetOptions(self, data):
        """
         Add device options
         @param data: data dict()
        """
        command = ''
        reportMediaNeeded = False
        for item in data:
            val = str(item['value'])
            if item['option'] == 'sos_phone_1':
                command += ',G0=' + val
                reportMediaNeeded = True
            elif item['option'] == 'sos_phone_2':
                command += ',G1=' + val
                reportMediaNeeded = True
            elif item['option'] == 'sos_phone_3':
                command += ',G2=' + val
                reportMediaNeeded = True
            elif item['option'] == 'sos_phone_4':
                command += ',G3=' + val
                reportMediaNeeded = True
            elif item['option'] == 'sos_phone_5':
                command += ',G4=' + val
                reportMediaNeeded = True
            elif item['option'] == 'sos_phone_6':
                command += ',G5=' + val
                reportMediaNeeded = True

        if reportMediaNeeded:
            command += ',H0=03'

        return command

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass
