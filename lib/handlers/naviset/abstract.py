# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset base class for other Naviset firmware
@copyright 2012-2013, Maprox LLC
'''


import json
from datetime import datetime
from struct import pack

import time

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.naviset.packets as packets
from lib.ip import get_ip

# ---------------------------------------------------------------------------

class NavisetHandler(AbstractHandler):
    """
     Base handler for Naviset protocol
    """
    _packetsFactory = packets.PacketFactory

    # private buffer for headPacket data
    __headPacketRawData = None

    __imageResolution = packets.IMAGE_RESOLUTION_640x480
    __imageReceivingConfig = None
    __packNum = 0

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        self._packetsFactory = packets.PacketFactory()
        return super(NavisetHandler, self).initialization()

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

        #self.sendCommand(packets.CommandGetStatus())
        #self.sendCommand(packets.CommandGetPhones())
        
        #b'\x01868204003057949'
        #self.sendCommand(packets.CommandGetImei())
        #self.sendCommand(packets.CommandGetRegisteredIButtons())
        #self.sendCommand(packets.CommandSwitchSecurityMode({'securityMode': 0}))
        #self.sendCommand(packets.CommandGetTrackParams())
        

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

        # Automatic image request each 5 minutes
        #diff = datetime.now() - \
        #    self.__imageReceivingConfig['lastChunkReceivedTime']
        #if diff.seconds > 60 * 5: # 5 minutes
        #    self.__imageReceivingConfig = None
        #    self.sendCommand(packets.CommandGetImage({
        #        "type": self.__imageResolution
        #    }))

        if not isinstance(packet, packets.PacketAnswerCommandGetImage):
            return

        config = self.__imageReceivingConfig
        if packet.code == packets.IMAGE_ANSWER_CODE_SIZE:
            log.info('Image transfer is started.')
            log.info('Size of image is %d bytes', packet.imageSize)
            config['imageSize'] = packet.imageSize
            config['bytesReceived'] = 0
            config['imageParts'] = {}
        elif packet.code == packets.IMAGE_ANSWER_CODE_DATA:
            log.debug('Image transfer in progress...')
            chunkLength = len(packet.chunkData)
            if chunkLength == 0:
                log.debug('Chunk #%d (%d bytes). Null chunk - skip it...',
                    packet.chunkNumber, chunkLength)
            else:
                config['bytesReceived'] += chunkLength
                config['imageParts'][packet.chunkNumber] = packet.chunkData
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

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = NavisetHandler(pipe.TestManager(), None)

    def test_packetData(self):
        h = self.handler
        config = h.getInitiationConfig({
            "identifier": "0123456789012345",
            "host": "trx.maprox.net",
            "port": 21200
        })
        self.assertEqual(config['device'], {
            'login': '',
            'password': ''
        })
        #data = h.getInitiationData(config)
        #self.assertEqual(data, [{
        #    'message': 'COM3 1234,' + str(get_ip()) + ',21200'
        #}, {
        #    'message': 'COM13 1234,1,,,#'
        #}])
        #message = h.getTaskData(321312, data)
        #self.assertEqual(message, {
        #    "id_action": 321312,
        #    "data": json.dumps(data)
        #})
    
    def test_processData(self):
        h = self.handler
        data = (
            b'\xdcC\x01\x00\xff\xffh)\x8f\xf0\\Q\x10\xe0l,\x03\xe8\xbc' +
            b'\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\x98, \r%\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00i)\x08\xf1\\Q\x10' +
            b'\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08' +
            b'\x98,\x01\r$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80' +
            b'\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00j)\x81\xf1\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00' +
            b'\x00\x00\x00\xff\x08\x98,&\r$\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80' +
            b'\x80\x80\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00k)\xfa\xf1\\Q\x10\xe0l,\x03\xe8\xbc' +
            b'\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\xba,\xdc\x0c$\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00l)s\xf2\\Q\x10\xe0l,\x03' +
            b'\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\xba,\x01\r$' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00m)\xec\xf2\\Q\x10\xe0l,' +
            b'\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\x98,' +
            b'\xf5\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00' +
            b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00n)e\xf3\\Q\x10' +
            b'\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff(\xba,' +
            b'\xdc\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00' +
            b'\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00o)\xde\xf3\\' +
            b'Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff' +
            b'\x08\x98,\x0e\r%\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80' +
            b'\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00p)W\xf4' +
            b'\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00' +
            b'\xff\x08\x98,\xef\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80' +
            b'\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'q)\xd0\xf4\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\x08\x98,-\r$\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80' +
            b'\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00r)I\xf5\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\x08\x98,\x0e\r%\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80' +
            b'\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00s)\xc2\xf5\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00' +
            b'\x00\x00\x00\xff\x08\xba,\xef\x0c$\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80' +
            b'\x80\x80\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00=\xa9'
        )
        
        h.processData(data)
        packets = h.getStore().get_stored_packets()
        
        
        self.assertEqual(len(packets), 12)
        
        packetItem = packets[3]
        self.assertEqual(packetItem['speed'], 0.0)
        self.assertEqual(packetItem['latitude'], 53.243104)
        self.assertEqual(packetItem['longitude'], 50.1834)
        self.assertEqual(packetItem['satellitescount'], 16)
        
        self.assertEqual(str(datetime.strptime(packetItem['time'],('%Y-%m-%dT%H:%M:%S.%f'))), '2013-04-04 03:22:34')
        
        packetItem2 = packets[6]
        
        self.assertEqual(packetItem2['speed'], 0)
        self.assertEqual(packetItem2['satellitescount'], 16)
        self.assertEqual(packetItem2['sensors']['int_temperature'], 36)
        self.assertEqual(packetItem2['sensors']['ext_battery_voltage'], 11450)
        self.assertEqual(packetItem2['sensors']['sat_antenna_connected'], 1)
        