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
import lib.handlers.atrack.packets as packets
import binascii

# ---------------------------------------------------------------------------

class AtrackHandler(AbstractHandler):
    """
     Base handler for ATrack protocol
    """
    _packetsFactory = packets.PacketFactory

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """

        protocolPackets = self._packetsFactory.getPacketsFromBuffer(data)
        for protocolPacket in protocolPackets:
            self.processProtocolPacket(protocolPacket)

        return super(AtrackHandler, self).processData(data)

    def processProtocolPacket(self, protocolPacket):
        """
         Process ATrack packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: ATrack protocol packet
        """
        if isinstance(protocolPacket, packets.PacketKeepAlive):
            log.debug('Keep alive packet received')

        # sends the acknowledgment
        self.sendAcknowledgement(protocolPacket)

        #if not self.uid:
        #    self.sendCommand(packets.PacketCommand('UNID'))

    def sendCommand(self, command):
        """
         Sends command to the device
         @param command: packets.PacketCommand
         @return:
        """
        self.send(command.rawData + b'\r\n')

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.BasePacket} subclass
        """
        buf = self.getAckPacket(packet)
        if not buf:
            return None
        log.info("Send acknowledgement: h" + binascii.hexlify(buf).decode())
        return self.send(buf)

    def getAckPacket(self, packet):
        """
         Returns acknowledgement buffer value
         @param packet: a L{packets.Packet} subclass
        """
        answer = packet
        if isinstance(packet, packets.PacketKeepAlive):
            pass
        elif isinstance(packet, packets.PacketData):
            answer = packets.PacketKeepAlive({
                'unitId': self.uid,
                'sequenceId': 1
            })
        else:
            return None
        return answer.rawData

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