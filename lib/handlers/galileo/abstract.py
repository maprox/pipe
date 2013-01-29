# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Galileo base class for other Galileo firmware
@copyright 2012, Maprox LLC
'''

import time, datetime
from struct import unpack, pack, calcsize

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.galileo.packets as packets

# ---------------------------------------------------------------------------

class GalileoHandler(AbstractHandler):
    """
     Base handler for Galileo protocol
    """
    __commands = {}
    __commands_num_seq = 0
    __imageReceivingConfig = None
    __packNum = 0

    # private buffer for headPacket data
    __headPacketRawData = None

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """
        if (self.__packNum == 1) and (self.__imageReceivingConfig is None):
            self.sendCommand("Makephoto 1")
        self.__packNum += 1

        protocolPackets = packets.Packet.getPacketsFromBuffer(data)
        for protocolPacket in protocolPackets:
            self.processProtocolPacket(protocolPacket)

        if self.__imageReceivingConfig is None:
            return super(GalileoHandler, self).processData(data)

    def processProtocolPacket(self, protocolPacket):
        """
         Process galileo packet.
         @param protocolPacket: Galileo protocol packet
        """
        observerPackets = self.translate(protocolPacket)
        self.sendAcknowledgement(protocolPacket)
        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        if protocolPacket.header == 1:
            self.__headPacketRawData = protocolPacket.rawData

        if protocolPacket.hasTag(0xE1):
            log.info('Device answer is "' +
                protocolPacket.getTag(0xE1).getValue() + '".')

        if len(observerPackets) > 0:
            if 'uid' in observerPackets[0]:
                self.headpack = observerPackets[0]
                self.uid = self.headpack['uid']
                log.info('HeadPack is stored.')
                return

        if protocolPacket.header == 4:
            return self.receiveImage(protocolPacket)

        log.info('Location packet not found. Exiting...')
        if len(observerPackets) == 0: return

        # MainPack
        for packet in observerPackets:
            packet.update(self.headpack)

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)

    def sendCommand(self, command):
        """
         Sends command to the tracker
         @param command: Command string
        """
        log.info('Sending "' + command + '"...')
        packet = packets.Packet()
        packet.header = 1
        packet.addTag(0x03, self.headpack['uid'])
        packet.addTag(0x04, self.headpack['uid2'])
        packet.addTag(0xE0, self.__commands_num_seq)
        packet.addTag(0xE1, command)
        self.send(packet.rawData)
        # save sended command in local dict
        self.__commands[self.__commands_num_seq] = packet
        self.__commands_num_seq += 1 # increase command number sequence

    def receiveImage(self, packet):
        """
         Receives an image from tracker.
         Sends it to the observer server, when totally received.
        """
        if (packet == None) or (packet.body == None) or (len(packet.body) == 0):
            log.error('Empty image packet. Transfer aborted!')
            return

        config = self.__imageReceivingConfig
        partnum = packet.body[0]
        if self.__imageReceivingConfig is None:
            self.__imageReceivingConfig = {
              'imageparts': {}
            }
            config = self.__imageReceivingConfig
            log.info('Image transfer is started.')
        else:
            if len(packet.body) > 1:
                log.debug('Image transfer in progress...')
                log.debug('Size of chunk is %d bytes', len(packet.body) - 1)
            else:
                imageData = b''
                imageParts = self.__imageReceivingConfig['imageparts']
                for num in sorted(imageParts.keys()):
                    imageData += imageParts[num]
                self.sendImages([{
                  'mime': 'image/jpeg',
                  'content': imageData
                }])
                self.__imageReceivingConfig = None
                log.debug('Transfer complete.')
                return

        imageData = packet.body[1:]
        config['imageparts'][partnum] = imageData

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        packets = []
        if (data == None): return packets
        if (data.tags == None): return packets

        packet = {'sensors': {}}
        prevNum = 0
        for tag in data.tags:
            num = tag.getNumber()

            if (num < prevNum):
                packets.append(packet)
                packet = {'sensors': {}}

            prevNum = num
            value = tag.getValue()
            #print(num, value)
            if (num == 3): # IMEI
                packet['uid'] = value
            elif (num == 4): # CODE
                packet['uid2'] = value
            elif (num == 32): # Timestamp
                packet['time'] = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif (num == 48): # Satellites count, Correctness, Latitude, Longitude
                packet.update(value)
            elif (num == 51): # Speed, Azimuth
                packet.update(value)
            elif (num == 52): # Altitude
                packet['altitude'] = value
            elif (num == 53): # HDOP
                packet['hdop'] = value
            elif (num == 64): # Status
                packet.update(value)
                packet['sensors']['acc'] = value['acc']
                packet['sensors']['sos'] = value['sos']
                packet['sensors']['extbattery_low'] = value['extbattery_low']
            elif (num == 80): # Analog input 0
                packet['sensors']['analog_input0'] = value

            #TEMPORARILY COMMENTED (TO MUCH UNUSED DATA)
            #elif (num == 81): # Analog input 1
            #  packet['sensors']['analog_input1'] = value
            #elif (num == 82): # Analog input 2
            #  packet['sensors']['analog_input2'] = value
            #elif (num == 83): # Analog input 3
            #  packet['sensors']['analog_input3'] = value

        packets.append(packet)
        return packets

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
        """
        buf = self.getAckPacket(packet.crc)
        log.info("Send acknowledgement, crc = %d" % packet.crc)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, crc):
        """
          Returns acknowledgement buffer value
        """
        return pack('<BH', 2, crc)

    def processCommandExecute(self, task, data):
        """
         Execute command for the device
         @param task: id task
         @param data: data dict()
        """
        log.info('Observer is sending a command:')
        log.info(data)
        self.sendCommand(data['command'])

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
        pass

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_packetData(self):
        import kernel.pipe as pipe
        h = GalileoHandler(pipe.Manager(), None)
        data = b'\x01"\x00\x03868204000728070\x042\x00' \
             + b'\xe0\x00\x00\x00\x00\xe1\x08Photo ok\x137'
        protocolPackets = packets.Packet.getPacketsFromBuffer(data)
        for packet in protocolPackets:
            self.assertEqual(packet.header, 1)
