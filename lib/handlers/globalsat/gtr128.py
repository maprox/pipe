# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globalsat GTR-128/GTR-129
@copyright 2009-2013, Maprox LLC
"""

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handlers.globalsat.abstract import GlobalsatHandler

class Handler(GlobalsatHandler):
    """ Globalsat. GTR-128/GTR-129 """

    confSectionName = "globalsat.gtr128"
    reportFormat = "SPRXYAB27GHKLMnaic*U!"

    def translateConfigOptions(self, send, options):
        """
         Translate gps-tracker parsed options to observer format
         @param send: {string[]} data to send
         @param options: {string[]} parsed options
        """
        send = GlobalsatHandler.translateConfigOptions(self, send, options)
        if 'Ri' in options:
            send['freq_mov'] = options['Ri']
        if 'Ra' in options:
            send['freq_idle'] = options['Ra']
        if 'Ro' in options:
            send['send_mov'] = options['Ro']
        if 'S8' in options:
            send['send_by_angle'] = options['S8']

        return send

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        packet = GlobalsatHandler.translate(self, data)
        sensor = packet['sensors'] or {}
        for char in data:
            value = data[char]
            if value == '': value = '0'
            if char == "a":
                sensor['ain0'] = float(value)
            if char == "c":
                sensor['gsm_signal_strength'] = float(value)
            if char == "n":
                batteryLevel = self.formatBatteryLevel(value)
                packet['batterylevel'] = batteryLevel # old version
                sensor['int_battery_voltage'] = batteryLevel # new version
        packet['sensors'] = sensor
        return packet

    def addCommandSetOptions(self, data):
        """
         Add device options
         @param data: data dict()
        """
        command = GlobalsatHandler.addCommandSetOptions(self, data)
        for item in data:
            val = str(item['value'])
            if item['option'] == 'freq_mov':
                command += ',Ri=' + val
            elif item['option'] == 'freq_idle':
                command += ',Ra=' + val
            elif item['option'] == 'send_mov':
                command += ',Ro=' + val
            elif item['option'] == 'send_by_angle':
                command += ',S8=' + val
        return command

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = Handler(pipe.Manager(), None)

    def test_inputData(self):
        h = self.handler
        data = 'GSr,012896007472407,0000,8,8080,8080,3,130313,084744,' + \
               'E03739.6939,N5547.2671,134,10.92,264,9,1.0,13660mV,0,0,21*77!'
        rc = h.re_compiled['report']
        m = rc.search(data, 0)
        self.assertIsNotNone(m)
        packet = h.translate(m.groupdict())
        self.assertEqual(packet['uid'], "012896007472407")

    def test_bufferData(self):
        h = self.handler
        data = 'GSb,012896007472407,0040,j,2080,1,010109,000049,' + \
               'E00000.0000,N0000.0000,0,0.00,0,0,0.0,0,50%,0,0,' + \
               '0,0,0,00,00,00,00,*1d!'
        rc = h.re_compiled['report']
        m = rc.search(data, 0)
        self.assertIsNone(m)

    def test_inputDataCorrupted(self):
        h = self.handler
        data = 'GSd,012896006644246,0000,5,8080,8080,3,190613,081637,' + \
               'E04841.5477,N5307.2988,46,0.06,248,8,1.3,12420mV,0,0,*78!'
        rc = h.re_compiled['report']
        m = rc.search(data, 0)
        self.assertIsNotNone(m)
        data_device = m.groupdict()
        packet = h.translate(data_device)
        self.assertEqual(packet['uid'], "012896006644246")
        cs1 = str.upper(data_device['checksum'])
        cs2 = str.upper(h.getChecksum(data_device['line']))
        self.assertEqual(cs1, cs2)


