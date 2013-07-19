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
    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        config = {}
        if conf.has_section('settings'):
            section = conf['settings']
            for key in section.keys():
                config[key] = section[key]
        self._packetsFactory = packets.PacketFactory(config)
        return super(AtrackHandler, self).initialization()

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
    
    def setUpFactory(self):
        """
        Method is taken from atrack.packets
        Used to create factory with configs
        Configs are needed to test the packets processing (test_processData)
        """
        from lib.handlers.atrack.packets import PacketFactory
        from configparser import ConfigParser
        conf = ConfigParser()
        conf.optionxform = str
        conf.read('conf/handlers/atrack.ax5.conf')
        section = conf['settings']
        config = {}
        for key in section.keys():
            config[key] = section[key]

        self.factory = PacketFactory(config)
    
    def setUp(self):
        import kernel.pipe as pipe
        self.handler = AtrackHandler(pipe.TestManager(), None)
        self.setUpFactory()

    def test_packetData(self):
        h = self.handler
    
    def test_processData(self):
        h = self.handler
        h._packetsFactory = self.factory
        
        data = (
            b'@P\x07(\x00U\x00\x04\x00\x01A\x04\xd8\xdd\x8f)Q\x97\xd7\x7f' +
            b'Q\x97\xd7\x7fQ\x99\xcb\xc3\x02=B\xd3\x03Sjc\x01\x13\x02\x00' +
            b'\x00\x0bP\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x06\x00\x82\x0br\x8f\x1ew\x00\x00a\xaa\x14\x00\x00' +
            b'\x00\xbd\x00\x00\x08\x00\x00\x00\x00\x00\x00\xff\xd8\x00\x00' +
            b'\x00\x00\x00\x00'
            )
        
        h.processData(data)
        
        stored_packets = h.getStore().get_stored_packets()
        
        self.assertEqual(len(stored_packets), 1)
        packet = stored_packets[0]
        
        self.assertEqual(len(packet), 14)
        self.assertEqual(packet["uid"], '352964050784041')
        self.assertEqual(packet["time_rtc"], '2013-05-18T19:33:19.000000')
        self.assertEqual(packet["sensors"]["gsm_status"], 8)
        
        

        
        
