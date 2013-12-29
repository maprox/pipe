# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Ime base class for other Ime firmware
@copyright 2012-2013, Maprox LLC
"""

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.ime.packets as packets
import lib.handlers.ime.commands as commands

# ---------------------------------------------------------------------------

class ImeHandler(AbstractHandler):
    """
     Base handler for Ime protocol
    """
    __headPacketRawData = None  # private buffer for headPacket data

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        super(ImeHandler, self).initialization()
        self._packetsFactory = packets.PacketFactory()
        self._commandsFactory = commands.CommandFactory()

    def processProtocolPacket(self, protocolPacket):
        """
         Process Ime packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Ime protocol packet
        """

        self.sendAcknowledgement(protocolPacket)

        self.isHeadPacket = False
        if isinstance(protocolPacket, packets.ImePacketLogin):
            log.info('[%s] Header is stored.', self.handlerId)
            self.uid = protocolPacket.deviceImei
            self.isHeadPacket = True

        if not isinstance(protocolPacket, packets.ImePacketData):
            return

        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('[%s] Location packet not found. Exiting...',
                     self.handlerId)
            return

        log.info(observerPackets)
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
         @param protocolPacket: Ime protocol packet
        """
        packetsList = []
        if protocolPacket is None: return packetsList
        if not isinstance(protocolPacket, packets.ImePacketData):
            return packetsList
        packet = {'uid': self.uid}
        packet.update(protocolPacket.params)
        packet['time'] = protocolPacket.params['time'].strftime(
            '%Y-%m-%dT%H:%M:%S.%f')
        # sensors
        sensor = packet['sensors'] or {}
        self.setPacketSensors(packet, sensor)
        packetsList.append(packet)
        return packetsList

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: {packets.ImePacket} subclass
        """
        if not isinstance(packet, packets.ImePacketLogin):
            return
        cmd = commands.ImeCommandLoginConfirm({
            'identifier': packet.deviceImei
        })
        self.send(cmd.getData())

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
from lib.crc16 import Crc16


class TestCase(unittest.TestCase):
    def setUp(self):
        packets.ImeBase.fnChecksum = Crc16.calcCCITT_Kermit
        packets.ImeBase._fmtChecksum = '<H'
        import kernel.pipe as pipe

        self.handler = ImeHandler(pipe.TestManager(), None)