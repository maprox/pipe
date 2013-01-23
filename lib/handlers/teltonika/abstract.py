# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika FMXXXXX base class
@copyright 2013, Maprox LLC
'''


import json
from struct import pack

from kernel.logger import log
from kernel.config import conf
from lib.handler import AbstractHandler
import lib.consts as consts
import binascii
from urllib.parse import urlencode
from urllib.request import urlopen
#import lib.handlers.teltonika.packets as packets

# ---------------------------------------------------------------------------

class TeltonikaHandler(AbstractHandler):
    """
     Base handler for Teltonika FMXXXXX protocol
    """

    # private buffer for headPacket data
    __headPacketRawData = None

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """
        """
        protocolPackets = packets.PacketFactory.getPacketsFromBuffer(data)
        for protocolPacket in protocolPackets:
            self.processProtocolPacket(protocolPacket)
        """

        return super(TeltonikaHandler, self).processData(data)

    def processProtocolPacket(self, protocolPacket):
        """
         Process naviset packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Naviset protocol packet
        """
        """
        self.sendAcknowledgement(protocolPacket)
        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        if isinstance(protocolPacket, packets.PacketHead):
            log.info('HeadPack is stored.')
            self.__headPacketRawData = protocolPacket.rawData
            self.uid = protocolPacket.deviceIMEI
            return

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('Location packet not found. Exiting...')
            return

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)
        """
        pass

    def sendCommand(self, command):
        """
         Sends command to the tracker
         @param command: Command string
        """
        log.info('Sending "' + command + '"...')
        log.info('[IS NOT IMPLEMENTED]')

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
         @param protocolPacket: Naviset protocol packet
        """
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
            list.append(packet)
            #packet['sensors']['acc'] = value['acc']
            #packet['sensors']['sos'] = value['sos']
            #packet['sensors']['extbattery_low'] = value['extbattery_low']
            #packet['sensors']['analog_input0'] = value
        return list
        """
        pass

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.Packet} subclass
        """
        """
        buf = self.getAckPacket(packet)
        log.info("Send acknowledgement, crc = %d" % packet.crc)
        return self.send(buf)
        """
        pass

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: a L{packets.Packet} subclass
        """
        return b'\x01' + pack('<H', packet.crc)

    def processCommandExecute(self, task, data):
        """
         Execute command for the device
         @param task: id task
         @param data: data dict()
        """
        log.info('Observer is sending a command:')
        log.info(data)
        self.sendCommand(data['command'])

    @classmethod
    def packString(cls, value):
        strLen = len(value)
        result = pack('>B', strLen)
        if strLen > 0:
            result += value.encode()
        return result

    def getInitiationSmsBuffer(self, data):
        """
         Returns initiation sms buffer
         @param data:
         @return:
        """
        # TP-UDH
        pushSmsPort = 0x07D1 # WDP Port listening for “push” SMS
        buffer = b'\x06\x05\x04'
        buffer += pack('>H', pushSmsPort)
        buffer += b'\x00\x00'

        # TP-UD
        buffer += self.packString(data['device']['login'])
        buffer += self.packString(data['device']['password'])
        buffer += self.packString(data['host'])
        buffer += pack('>H', data['port'])
        buffer += self.packString(data['gprs']['apn'])
        buffer += self.packString(data['gprs']['username'])
        buffer += self.packString(data['gprs']['password'])

        return buffer

    #def getInitiationData(self, input):


    def getInitiationData(self, config):
        """
         Returns initialization data for SMS wich will be sent to device
         @param config: config dict
         @return: array of dict or dict
        """
        buffer = self.getInitiationSmsBuffer(config)
        data = [{
            'message': binascii.hexlify(buffer).decode(),
            'bin': consts.SMS_BINARY_HEX_STRING,
            'flash': True
        }]
        return data

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        pass

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        #current_db = db.get(self.uid)
        #if not current_db.isReadingSettings():
        #    pass
        pass

# ===========================================================================
# TESTS
# ===========================================================================

import unittest

class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_packetData(self):
        import kernel.pipe as pipe
        h = TeltonikaHandler(pipe.Manager(), None)
        config = h.getInitiationConfig({
            "identifier": "0123456789012345",
            "host": "trx.maprox.net",
            "port": 21200
        })
        data = h.getInitiationData(config)
        self.assertEqual(data, [{
            'bin': consts.SMS_BINARY_HEX_STRING,
            'message': '06050407d1000000000e7472782e6d6' + \
                       '170726f782e6e657452d0000000',
            'flash': True
        }])
        message = h.getTaskData(321312, data)
        self.assertEqual(message, {
            "id_action": 321312,
            "data": data
        })