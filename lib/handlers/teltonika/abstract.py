# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika FMXXXXX base class
@copyright 2013, Maprox LLC
'''


import os
import binascii
from struct import pack

from kernel.logger import log
from kernel.config import conf
from kernel.dbmanager import db
from lib.handler import AbstractHandler
import lib.consts as consts
import binascii
import lib.handlers.teltonika.packets as packets
import lib.handlers.teltonika.commands as commands

# ---------------------------------------------------------------------------

class TeltonikaHandler(AbstractHandler):
    """
     Base handler for Teltonika FMXXXXX protocol
    """
    __headPacketRawData = None # private buffer for headPacket data

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        super(TeltonikaHandler, self).initialization()
        self._packetsFactory = packets.PacketFactory()
        self._commandsFactory = commands.CommandFactory()

    def processProtocolPacket(self, protocolPacket):
        """
         Process teltonika packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Teltonika protocol packet
        """
        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        if isinstance(protocolPacket, packets.PacketHead):
            log.info('HeadPack is stored.')
            self.__headPacketRawData = protocolPacket.rawData
            self.uid = protocolPacket.deviceImei

        if not self.uid:
            return log.error('HeadPack is not found!')

        # try to configure this tracker
        if self.configure():
            return

        # sends the acknowledgment
        self.sendAcknowledgement(protocolPacket)

        if isinstance(protocolPacket, packets.PacketHead):
            return

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('Location packet not found. Exiting...')
            return

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)

    def configure(self):
        current_db = db.get(self.uid)
        if not current_db.has('config'):
            return False
        data = current_db.get('config')
        self.send(data)
        log.debug('Configuration data sent = %s', data)
        config = packets.TeltonikaConfiguration(data)
        answer = b''
        try:
            log.debug('Waiting for the answer from device...')
            answer = self.recv()
        except Exception as E:
            log.error(E)
        current_db.remove('config')
        return config.isCorrectAnswer(answer)

    def receiveImage(self, packet):
        """
         Receives an image from tracker.
         Sends it to the observer server, when totally received.
        """
        log.error('Image receiving...')
        log.info('[IS NOT IMPLEMENTED]')

    def translate(self, protocolPacket):
        """
         Translate gps-tracker data to observer pipe format
         @param protocolPacket: Teltonika protocol packet
        """
        list = []
        if (protocolPacket == None): return list
        if not isinstance(protocolPacket, packets.PacketData):
            return list
        if (len(protocolPacket.AvlDataArray.items) == 0):
            return list
        for item in protocolPacket.AvlDataArray.items:
            packet = {'uid': self.uid}
            packet.update(item.params)
            packet['time'] = packet['time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            packet['hdop'] = 1 # temporarily manual value of hdop
            # sensors
            sensor = {}
            if 'sensors' in packet:
                sensor = packet['sensors']
            sensor['sat_count'] = packet['satellitescount']
            self.setPacketSensors(packet, sensor)
            list.append(packet)
        return list

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.BasePacket} subclass
        """
        buf = self.getAckPacket(packet)
        log.info("Send acknowledgement: h" + binascii.hexlify(buf).decode())
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: a L{packets.Packet} subclass
        """
        if isinstance(packet, packets.PacketHead):
            return b'\x01'
        else:
            return pack('>L', len(packet.AvlDataArray.items))

    @classmethod
    def packString(cls, value):
        strLen = len(value)
        result = pack('>B', strLen)
        if strLen > 0:
            result += value.encode()
        return result

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
import kernel.pipe as pipe

class TestCase(unittest.TestCase):

    def setUp(self):
        self.handler = TeltonikaHandler(pipe.TestManager(), None)
        pass

    def test_packetAcknowledgement(self):
        h = self.handler
        data = b'\x00\x00\x00\x00\x00\x00\x00\x2c\x08\x01\x00\x00\x01\x13' +\
               b'\xfc\x20\x8d\xff\x00\x0f\x14\xf6\x50\x20\x9c\xca\x80\x00' +\
               b'\x6f\x00\xd6\x04\x00\x04\x00\x04\x03\x01\x01\x15\x03\x16' +\
               b'\x03\x00\x01\x46\x00\x00\x01\x5d\x00\x01\x00\x00\xcf\x77'
        packet = packets.PacketData(data)
        self.assertEqual(h.getAckPacket(packet), b'\x00\x00\x00\x01')
        packet = h._packetsFactory.getInstance(b'\x00\x0f012896001609129')
        self.assertEqual(h.getAckPacket(packet), b'\x01')

    def test_processData(self):
        h = self.handler
        data = b'\x00\x0f012896001609129' +\
               b'\x00\x00\x00\x00\x00\x00\x02\xf1\x08\x19\x00\x00\x01<' +\
               b'\x95@\xd8\xbe\x00\x16BE\xe0!#,\xc0\x01#\x00\x00\x07\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x957\xadz\x00' +\
               b'\x16BE\xe0!#,\xc0\x01\x1c\x00\x00\x07\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x01<\x95\'\x19\xa6\x00\x16B=' +\
               b'\xa0!#.\xc0\x00\xf6\x00\x00\x08\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x95\x1d\xeff\x00\x16B=\xa0!#.\xc0' +\
               b'\x01\x07\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x95\x14\xc7\xa6\x00\x16B=\xa0!#.\xc0\x00' +\
               b'\xe4\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x95\x0b\x9cb\x00\x16B=\xa0!#.\xc0\x00\xbe\x00' +\
               b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x95\x02t\xa2\x00\x16B=\xa0!#.\xc0\x00\xf1\x00\x00\x06' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xf9L' +\
               b'\xe2\x00\x16B=\xa0!#.\xc0\x00\xf0\x00\x00\x06\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xf0%"\x00\x16' +\
               b'B=\xa0!#.\xc0\x01\x0b\x00\x00\x08\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x01<\x94\xe6\xfa\x10\x00\x16B=\xa0' +\
               b'!#.\xc0\x00\xf3\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x01<\x94\xdd\xd2P\x00\x16B=\xa0!#.\xc0\x00' +\
               b'\xef\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x94\xd4\xaa\x90\x00\x16B=\xa0!#.\xc0\x00\xef' +\
               b'\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94\xcb\x82\xd0\x00\x16B=\xa0!#.\xc0\x00\xd3\x00' +\
               b'\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x94\xc2Z\xfc\x00\x16B=\xa0!#.\xc0\x00\xdf\x00\x00\x08' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xb93<' +\
               b'\x00\x16B=\xa0!#.\xc0\x00\xe1\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xb0\x0br\x00\x16' +\
               b'B4\x80!#(\xc0\x00\xf6\x00\x00\t\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x94\xa6\xe3\xb2\x00\x16B4\x80!#(' +\
               b'\xc0\x00\xf0\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x01<\x94\x9c)\xcc\x00\x16B8\x80!#6\x80\x00' +\
               b'\xf1\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94\x93\x02\x0c\x00\x16B8\x80!#6\x80\x01\x0f\x00' +\
               b'\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x94\x89\xdaL\x00\x16B8\x80!#6\x80\x00\xbf\x00\x00\t\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94y\x82\xbe' +\
               b'\x00\x16B;\xe0!#1\x00\x00\xb0\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x01<\x94pZ\xfe\x00\x16B;' +\
               b'\xe0!#1\x00\x00\xe0\x00\x00\x07\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x94g/t\x00\x16B;\xe0!#1\x00\x00' +\
               b'\xfe\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94^\x03\xf4\x00\x16B;\xe0!#1\x00\x00\xfa\x00\x00' +\
               b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94T' +\
               b'\xdc4\x00\x16B7\x80!#2@\x01\x18\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x19\x00\x00\x1bb'
   
        h.processData(data)
        stored_packets = h.getStore().get_stored_packets()

        self.assertEqual(len(stored_packets), 25)
        packet = stored_packets[0]

        self.assertEqual(packet['uid'], '012896001609129')
        self.assertEqual(packet['altitude'], 291)
        self.assertEqual(packet['time'], '2013-02-01T10:15:20.510000')

        self.assertEqual(packet['sensors']['sat_count'], 7)
        self.assertEqual(packet['sensors']['altitude'], 291)
        