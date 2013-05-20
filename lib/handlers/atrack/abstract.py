# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack base class for other ATrack firmware
@copyright 2013, Maprox LLC
'''


from kernel.config import conf
from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.atrack.packets as packets
import binascii

# ---------------------------------------------------------------------------

class AtrackHandler(AbstractHandler):
    """
     Base handler for ATrack protocol
    """
    _packetsFactory = packets.PacketFactory

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        config = {}
        if conf.has_section(self.confSectionName):
            section = conf[self.confSectionName]
            for key in section.keys():
                config[key] = section[key]
        self._packetsFactory = packets.PacketFactory(config)
        return super(AtrackHandler, self).initialization()

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
            self.uid = protocolPacket.unitId
            log.debug('Keep alive packet received. UnitId = %s' % self.uid)

        # sends the acknowledgment
        self.sendAcknowledgement(protocolPacket)

        if not isinstance(protocolPacket, packets.PacketData):
            return

        if not self.uid:
            self.uid = protocolPacket.unitId
            log.debug('Data packet received. UnitId = %s' % self.uid)

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('Location packet not found. Exiting...')
            return

        log.info(observerPackets)
        self._buffer = protocolPacket.rawData
        self.store(observerPackets)

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
            answer = packets.PacketKeepAlive()
            answer.unitId = packet.unitId
            answer.sequenceId = packet.sequenceId
        else:
            return None
        return answer.rawData

    def translate(self, protocolPacket):
        """
         Translate gps-tracker data to observer pipe format
         @param protocolPacket: Atrack protocol packet
        """
        list = []
        if (protocolPacket == None): return list
        if not isinstance(protocolPacket, packets.PacketData):
            return list
        if (len(protocolPacket.items) == 0):
            return list
        for item in protocolPacket.items:
            packet = {'uid': self.uid}
            packet.update(item)
            packet['time'] = packet['time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            packet['time_rtc'] =\
                packet['time_rtc'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            packet['time_send'] =\
                packet['time_send'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            packet['altitude'] = item['sensors']['altitude']
            packet['satellitescount'] = item['sensors']['sat_count']
            # sensors
            sensor = packet['sensors'] or {}
            self.setPacketSensors(packet, sensor)
            list.append(packet)
        return list

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
