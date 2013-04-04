# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset base class for other Naviset firmware
@copyright 2012-2013, Maprox LLC
'''


import json
from datetime import datetime
from struct import pack

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.naviset.packets as packets
from lib.ip import get_ip

# ---------------------------------------------------------------------------

class NavisetHandler(AbstractHandler):
    """
     Base handler for Naviset protocol
    """

    # private buffer for headPacket data
    __headPacketRawData = None

    __imageResolution = packets.IMAGE_RESOLUTION_640x480
    __imageReceivingConfig = None
    __packNum = 0

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """
        try:
            protocolPackets = packets.PacketFactory.getPacketsFromBuffer(data)
            for protocolPacket in protocolPackets:
                self.processProtocolPacket(protocolPacket)
        except Exception as E:
            log.error("processData error: %s", E)

        return super(NavisetHandler, self).processData(data)

    def processProtocolPacket(self, protocolPacket):
        """
         Process naviset packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Naviset protocol packet
        """
        self.sendAcknowledgement(protocolPacket)
        self.receiveImage(protocolPacket)

        if isinstance(protocolPacket, packets.PacketHead):
            log.info('HeadPack is stored.')
            self.__headPacketRawData = protocolPacket.rawData
            self.uid = protocolPacket.deviceImei

        if not isinstance(protocolPacket, packets.PacketData):
            return

        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        observerPackets = self.translate(protocolPacket)
        if len(observerPackets) == 0:
            log.info('Location packet not found. Exiting...')
            return

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)

    def sendCommand(self, command):
        """
         Sends command to the tracker
         @param command: Command class
        """
        if isinstance(command, packets.Command):
            log.info('Sending command "%s"...', command.number)
            self.send(command.rawData)
        else:
            log.error('Incorrect command object')

    def receiveImage(self, packet):
        """
         Receives an image from tracker.
         Sends it to the observer server, when totally received.
        """
        if self.__imageReceivingConfig is None:
            self.__imageReceivingConfig = {
                'bytesReceived': 0,
                'lastChunkReceivedTime': datetime.now(),
                'imageParts': {}
            }

        diff = datetime.now() - \
            self.__imageReceivingConfig['lastChunkReceivedTime']
        if diff.seconds > 60 * 5: # 5 minutes
            self.__imageReceivingConfig = None
            self.sendCommand(packets.CommandGetImage({
                "type": self.__imageResolution
            }))

        if not isinstance(packet, packets.PacketAnswerCommandGetImage):
            return

        if self.__imageReceivingConfig is None:
            self.__imageReceivingConfig = {
                'bytesReceived': 0,
                'imageParts': {}
            }

        config = self.__imageReceivingConfig
        if packet.code == packets.IMAGE_ANSWER_CODE_SIZE:
            config['imageSize'] = packet.imageSize
            log.info('Image transfer is started.')
            log.info('Size of image is %d bytes', packet.imageSize)
        elif packet.code == packets.IMAGE_ANSWER_CODE_DATA:
            chunkLength = len(packet.chunkData)
            config['bytesReceived'] += chunkLength
            config['imageParts'][packet.chunkNumber] = packet.chunkData
            log.debug('Image transfer in progress...')
            log.debug('Chunk #%d (%d bytes). %d of %d bytes received.',
                packet.chunkNumber, chunkLength,
                config['bytesReceived'], config['imageSize'])
            if config['bytesReceived'] >= config['imageSize']:
                imageData = b''
                imageParts = self.__imageReceivingConfig['imageParts']
                for num in sorted(imageParts.keys()):
                    imageData += imageParts[num]
                log.debug('Transfer complete. Sending to the server...')
                self.sendImages([{
                    'mime': 'image/jpeg',
                    'content': imageData
                }])
                self.__imageReceivingConfig = None

        # remember time of last chunk to re-request image
        # if connection breaks down
        config['lastChunkReceivedTime'] = datetime.now()
        # send confirmation
        self.sendCommand(packets.CommandGetImage({
            "type": packets.IMAGE_PACKET_CONFIRM_OK
        }))

    def translate(self, protocolPacket):
        """
         Translate gps-tracker data to observer pipe format
         @param protocolPacket: Naviset protocol packet
        """
        list = []
        if (protocolPacket == None): return list
        if not isinstance(protocolPacket, packets.PacketData):
            return list
        if (len(protocolPacket.items) == 0):
            return list
        for item in protocolPacket.items:
            packet = {'uid': self.uid}
            #sensor = {}
            packet.update(item.params)
            packet['time'] = packet['time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
            #sensor['acc'] = item.params['acc']
            #sensor['sos'] = item.params['sos']
            #sensor['ext_battery_low'] = item.params['extbattery_low']
            #sensor['ain0'] = value
            list.append(packet)
        return list

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.Packet} subclass
        """
        buf = self.getAckPacket(packet)
        log.info("Send acknowledgement, checksum = %d" % packet.checksum)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: a L{packets.Packet} subclass
        """
        return b'\x01' + pack('<H', packet.checksum)

    def processCommandExecute(self, task, data):
        """
         Execute command for the device
         @param task: id task
         @param data: data dict()
        """
        log.info('Observer is sending a command:')
        log.info(data)
        self.sendCommand(data['command'])

    def getInitiationData(self, config):
        """
         Returns initialization data for SMS wich will be sent to device
         @param config: config dict
         @return: array of dict or dict
        """
        command0 = 'COM3 1234,' + str(get_ip()) + ',' + str(config['port'])
        command1 = 'COM13 1234,1,'+ config['gprs']['apn'] \
            + ',' + config['gprs']['username'] \
            + ',' + config['gprs']['password'] + '#'
        return [{
            "message": command0
        }, {
            "message": command1
        }]

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
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = NavisetHandler(pipe.Manager(), None)

    def test_packetData(self):
        h = self.handler
        config = h.getInitiationConfig({
            "identifier": "0123456789012345",
            "host": "trx.maprox.net",
            "port": 21200
        })
        data = h.getInitiationData(config)
        self.assertEqual(data, [{
            'message': 'COM3 1234,' + str(get_ip()) + ',21200'
        }, {
            'message': 'COM13 1234,1,,,#'
        }])
        message = h.getTaskData(321312, data)
        self.assertEqual(message, {
            "id_action": 321312,
            "data": json.dumps(data)
        })