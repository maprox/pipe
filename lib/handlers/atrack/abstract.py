# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack base class for other ATrack firmware
@copyright 2013, Maprox LLC
'''


import json
from datetime import datetime
from struct import pack

from kernel.logger import log
from lib.handler import AbstractHandler
from lib.ip import get_ip

# ---------------------------------------------------------------------------

class AtrackHandler(AbstractHandler):
    """
     Base handler for ATrack protocol
    """

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """
        try:
            log.debug(data.decode())
        except Exception as E:
            log.debug(data)
        #try:
        #    protocolPackets = packets.PacketFactory.getPacketsFromBuffer(data)
        #    for protocolPacket in protocolPackets:
        #        self.processProtocolPacket(protocolPacket)
        #except Exception as E:
        #    log.error("processData error: %s", E)

        #return super(AtrackHandler, self).processData(data)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = AtrackHandler(pipe.Manager(), None)

    def test_packetData(self):
        h = self.handler