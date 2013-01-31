# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika FMXXXX firmware
@copyright 2009-2013, Maprox LLC
'''

from kernel.logger import log
from lib.handlers.teltonika.abstract import TeltonikaHandler
import lib.handlers.teltonika.packets as packets

class Handler(TeltonikaHandler):
    """ Teltonika. FMXXXX configuration server """
    _confSectionName = "teltonika.fmxxxx"

    def processProtocolPacket(self, protocolPacket):
        """
         Process naviset packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Naviset protocol packet
        """
        if not self.__headPacketRawData:
            self.__headPacketRawData = b''
        if isinstance(protocolPacket, packets.PacketHead):
            log.info('HeadPack is received.')


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_format(self):
        pass
