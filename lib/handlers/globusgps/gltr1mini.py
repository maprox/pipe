# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globusgps GL-TR1-mini firmware
@copyright 2009-2013, Maprox LLC
"""

from lib.handlers.ime.abstract import ImeHandler
import lib.handlers.ime.packets as packets
from lib.crc16 import Crc16

# This is a spike-nail to substitute checksum calculation
packets.ImeBase._fmtChecksum = '<H'
packets.ImeBase.fnChecksum = Crc16.calcCCITT_Kermit

class Handler(ImeHandler):
    """ Globusgps. GL-TR1-mini """

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        packets.ImeBase.fnChecksum = Crc16.calcCCITT_Kermit
        packets.ImeBase._fmtChecksum = '<H'
        self.factory = packets.PacketFactory()

    def test_checksumStrange(self):
        packetsList = self.factory.getPacketsFromBuffer(
            b"$$\x00\x115\x96(\x01v1hP\x00S'\r\n"
        )
        p = packetsList[0]
        self.assertEqual(p.deviceImei, '35962801763168')

    def test_realAlarmPacket(self):
        packetsList = self.factory.getPacketsFromBuffer(
            b'$$\x00+5\x96(\x01v1h\x99\x99\x01,'
            b'|1.49|168.6|1100|055|100\xc3\x03'
            b'\r\n'
        )
        p = packetsList[0]
        self.assertEqual(p.deviceImei, '35962801763168')
        self.assertIsInstance(p, packets.ImePacketDataWithAlarm)
        self.assertEqual(p.alarmCode, packets.ALARM_SOS)
        self.assertEqual(p.params['sensors']['alarm_code'], packets.ALARM_SOS)
        self.assertEqual(p.params['sensors']['sos'], 1)