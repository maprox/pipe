# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Globalsat TR-151
@copyright 2009-2012, Maprox LLC
'''

import re
import json
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from kernel.dbmanager import db
from lib.handler import AbstractHandler
from lib.geo import Geo
from lib.ip import get_ip
from urllib.parse import urlencode
from urllib.request import urlopen


class Handler(AbstractHandler):
    """ Globalsat. TR-151 """

    _confSectionName = "naviset.protocolname"
    _reportFormat = "RAB27GHKLM"

    re_patterns = {
        'line': '\$(?P<S>\w+){fields}!',
        'field': ',(?P<{field}>{value})',
        'unknownField': '[\w\.]+',
        'report': {
            'A': '[1-3]',
            'B': '\d{6},\d{6}',
            '2': '[EW]\d{5}\.\d{4}',
            '7': '[NS]\d{4}\.\d{4}',
            'G': '\d+(\.\d+)?',
            'H': '\d+(\.\d+)?',
            'K': '\d+',
            'L': '\d+',
            'M': '\d+(\.\d+)?',
            'N': '\d+',
            'R': '\w'
        }
    }

    re_compiled = {
        'report': None
    }

    def __init__(self, store, thread):
        """
         Constructor
        """
        AbstractHandler.__init__(self, store, thread)
        self.__compileRegularExpressions()

    def __compileRegularExpressions(self):
        """
         Compiling of regular expressions
        """
        # Let's start with report format
        p = self.re_patterns
        fieldsStr = ""
        for char in self._reportFormat:
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
        return self

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
        """
        initialData = data

        # let's work with text data
        data = data.decode('utf-8')
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
            packetObserver = self.translate(data_device)
            packetObserver['__rawdata'] = m.group(0)
            log.info(packetObserver)
            self.uid = packetObserver['uid']
            self.store([packetObserver])
            position += len(m.group(0))
            m = rc.search(data, position)

        return super(Handler, self).processData(initialData)

    def processError(self, data):
        """
         OK. Our pattern doesn't match the socket or config data.
         The source of the problem can be in wrong report format.
        """
        log.error("Unknown data format...")

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.Packet} subclass
        """
        buf = self.getAckPacket(packet)
        log.info("Send acknowledgement, crc = %d" % packet.crc)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: Received packet
        """
        return b"$OK!"

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        packet = {}
        for char in data:
            value = data[char]
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
                packet['altitude'] = float(value)
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
            # Azimuth - driving direction
            elif char == "K":
                packet['azimuth'] = float(value)
            # HDOP (Horizontal Dilution of Precision)
            elif char == "M":
                packet['hdop'] = float(value)
            # Report Mode
            elif char == "A":
                if int(value) == 5:
                    packet['sensors'] = {}
                    packet['sensors']['sos'] = 1
        return packet

    def processCommandFormat(self, task, data):
        """
         Processing command to form config string
         @param task: id task
         @param data: request
        """
        data = json.loads(data)
        string = '?7,'\
                   + str(data['identifier'] or '') + ',7,'\
                   + str(data['port'] or conf.port) + ','\
                   + str(data['gprs']['apn'] or '') + ','\
                   + str(data['gprs']['username'] or '') + ','\
                   + str(data['gprs']['password'] or '') + ',,,'\
                   + '' + ','\
                   + '' + ','\
                   + str(data['host'] or get_ip()) + ','\
                   + '!'
        log.debug('Formatted string result: ' + string)
        message = {
            'result': string,
            'id_action': task
        }
        log.debug('Formatted string sent: '\
           + conf.pipeFinishUrl + urlencode(message))
        urlopen(conf.pipeFinishUrl, urlencode(message).encode('utf-8'))

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        pass

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        current_db = db.get(self.uid)
        if not current_db.isReadingSettings():
            pass


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_packetData(self):
        import kernel.pipe as pipe
        h = Handler(pipe.Manager(), None)
        data = "$355632004245866,1,1,040202,093633,E12129.2252," + \
            "N2459.8891,00161,0.0100,147,07,2.4!"
        rc = h.re_compiled['report']
        m = rc.search(data, 0)
        packet = h.translate(m.groupdict())
        self.assertEqual(packet['uid'], "355632004245866")
        self.assertEqual(packet['time'], "2002-02-04T09:36:33.000000")
        self.assertEqual(packet['altitude'], 161)
        self.assertEqual(packet['azimuth'], 147)
        self.assertEqual(packet['longitude'], 121.48708666666667)