# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Autolink base class for other Autolink firmware
@copyright 2012-2013, Maprox LLC
"""

from datetime import datetime
from struct import pack

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.autolink.packets as packets
import lib.handlers.autolink.commands as commands

from lib.broker import broker

# ---------------------------------------------------------------------------

class AutolinkHandler(AbstractHandler):
    """
     Base handler for Autolink protocol
    """
    __headPacketRawData = None # private buffer for headPacket data
    __imageReceivingConfig = None
    __packNum = 0

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        super(AutolinkHandler, self).initialization()
        self._packetsFactory = packets.PacketFactory()
        self._commandsFactory = commands.CommandFactory()

    def processProtocolPacket(self, protocolPacket):
        """
         Process autolink packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Autolink protocol packet
        """

        self.sendAcknowledgement(protocolPacket)

        self.isHeadPacket = False
        log.info('[%s] processProtocolPacket... isHead = %s',
            self.handlerId, self.isHeadPacket)
        if isinstance(protocolPacket, packets.PacketHead):
            log.info('[%s] HeadPack is stored.', self.handlerId)
            self.__headPacketRawData = protocolPacket.rawData
            self.uid = protocolPacket.deviceImei
            self.isHeadPacket = True

        if isinstance(protocolPacket, packets.PacketAnswer):
            log.info("[%s] Storing command answer packet: %s",
                self.handlerId, protocolPacket.__class__)
            broker.sendAmqpAnswer(self, protocolPacket)
            return

        if not isinstance(protocolPacket, packets.PacketData):
            return

        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('[%s] Location packet not found. Exiting...',
                self.handlerId)
            return

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)

    def needProcessCommands(self):
        """
         Returns false if we can not process commands
         @return: boolean
        """
        log.debug('[%s] needProcessCommands??? %s %s',
            self.handlerId, self.uid, self.isHeadPacket)
        return self.uid and not self.isHeadPacket

    def translate(self, protocolPacket):
        """
         Translate gps-tracker data to observer pipe format
         @param protocolPacket: Autolink protocol packet
        """
        list = []
        if (protocolPacket == None): return list
        if not isinstance(protocolPacket, packets.PacketData):
            return list
        if (len(protocolPacket.items) == 0):
            return list
        for item in protocolPacket.items:
            packet = {'uid': self.uid}
            packet.update(item.params)
            packet['time'] = packet['time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            # sensors
            sensor = packet['sensors'] or {}
            sensor['sat_count'] = packet['satellitescount']
            self.setPacketSensors(packet, sensor)
            list.append(packet)
        return list

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.Packet} subclass
        """
        buf = self.getAckPacket(packet)
        log.info("[%s] Send acknowledgement", self.handlerId)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: a L{packets.Packet} subclass
        """
        return b'\x01' + pack('<H', packet.checksum)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = AutolinkHandler(pipe.TestManager(), None)
