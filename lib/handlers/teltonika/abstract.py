# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika FMXXXXX base class
@copyright 2013, Maprox LLC
'''


import os
import binascii
from struct import pack
from lib.ip import get_ip

from kernel.logger import log
from kernel.config import conf
from kernel.dbmanager import db
from lib.handler import AbstractHandler
import lib.consts as consts
import binascii
import lib.handlers.teltonika.packets as packets

# ---------------------------------------------------------------------------

class TeltonikaHandler(AbstractHandler):
    """
     Base handler for Teltonika FMXXXXX protocol
    """
    _packetsFactory = packets.PacketFactory

    # private buffer for headPacket data
    __headPacketRawData = None

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        self._packetsFactory = packets.PacketFactory()
        return super(TeltonikaHandler, self).initialization()

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
         @param packnum: Number of socket packet (defaults to 0)
         @return: self
        """
        protocolPackets = self._packetsFactory.getPacketsFromBuffer(data)
        #print('processData output:')
        #print(protocolPackets[0].AvlDataArray.items[0].__dict__)
        self.getStore().stored_protocol_packets = protocolPackets
        for protocolPacket in protocolPackets:
            self.processProtocolPacket(protocolPacket)

        return super(TeltonikaHandler, self).processData(data)

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
         @param data: dict
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
        buffer += self.packString(str(get_ip()))
        buffer += pack('>H', data['port'])
        buffer += self.packString(data['gprs']['apn'])
        buffer += self.packString(data['gprs']['username'])
        buffer += self.packString(data['gprs']['password'])
        return buffer

    def getConfigurationSmsParts(self, data, config):
        """
         Returns initiation sms buffer
         @param data: dict
         @param config: Teltonika configuration packet buffer
         @return:
        """
        parts = []
        authLength = len(data['device']['login'] + data['device']['password'])
        headLength = 12 + authLength
        partLength = consts.SMS_BINARY_MAX_LENGTH - headLength
        partsCount = 1 + int(len(config) / partLength)
        # create configuration sms parts
        pushSmsPort = 0x07D1 # WDP Port listening for “push” SMS
        # TP-UDH
        header = b'\x06\x05\x04'
        header += pack('>H', pushSmsPort)
        header += b'\x00\x00'
        # TP-UD
        header += self.packString(data['device']['login'])
        header += self.packString(data['device']['password'])
        header += os.urandom(1) # transferId
        header += pack('>B', partsCount)
        # create configuration sms parts
        index = 0
        offset = 0
        while index < partsCount:
            buffer = header
            buffer += pack('>B', index) # current part number
            buffer += config[offset:offset + partLength]
            parts.append(buffer)
            index += 1
            offset += partLength
        return parts

    def getPushSmsData(self, config):
        """
         Creates push sms data (1st config method)
         @param config:
         @return:
        """
        # create config packet and save it to the database
        packet = self.getConfigurationPacket(config)
        current_db = db.get(config['identifier'])
        current_db.set('config', packet.rawData)
        log.info(packet.rawData)
        # create push-sms for configuration
        buffer = self.getInitiationSmsBuffer(config)
        data = [{
            'message': binascii.hexlify(buffer).decode(),
            'bin': consts.SMS_BINARY_HEX_STRING,
            'push': True
        }]
        return data

    def getConfigSmsData(self, config):
        """
         Creates config sms data (2nd config method)
         @param config:
         @return:
        """
        # create config packet and save it to the database
        packet = self.getConfigurationPacket(config)
        log.info(packet.rawData)
        # create push-sms for configuration
        parts = self.getConfigurationSmsParts(config, packet.rawData)
        data = []
        for buffer in parts:
            data.append({
                'message': binascii.hexlify(buffer).decode(),
                'bin': consts.SMS_BINARY_HEX_STRING
            })
        return data

    def getInitiationData(self, config):
        """
         Returns initialization data for SMS wich will be sent to device
         @param config: config dict
         @return: array of dict or dict
        """
        return self.getPushSmsData(config)

    def getConfigurationPacket(self, config):
        """
         Returns Teltonika configuration packet
         @param config: config dict
         @return:
        """
        packet = packets.TeltonikaConfiguration()
        packet.packetId = 1
        packet.addParam(packets.CFG_DEEP_SLEEP_MODE, 0)
        packet.addParam(packets.CFG_SORTING, packets.CFG_SORTING_ASC)
        packet.addParam(packets.CFG_ACTIVE_DATA_LINK_TIMEOUT, 20)
        packet.addParam(packets.CFG_TARGET_SERVER_IP_ADDRESS, str(get_ip()))
        packet.addParam(packets.CFG_TARGET_SERVER_PORT, str(config['port']))
        packet.addParam(packets.CFG_APN_NAME, config['gprs']['apn'])
        packet.addParam(packets.CFG_APN_USERNAME, config['gprs']['username'])
        packet.addParam(packets.CFG_APN_PASSWORD, config['gprs']['password'])
        packet.addParam(packets.CFG_SMS_LOGIN, config['device']['login'])
        packet.addParam(packets.CFG_SMS_PASSWORD, config['device']['password'])
        packet.addParam(packets.CFG_STOP_DETECTION_SOURCE,
            packets.CFG_STOP_DETECTION_VAL_MOVEMENT_SENSOR)
        packet.addParam(packets.CFG_GPRS_CONTENT_ACTIVATION, 1) # Enable
        packet.addParam(packets.CFG_OPERATOR_LIST, '25002') # MegaFON
        # on stop config
        packet.addParam(packets.CFG_VEHICLE_ON_STOP_MIN_SAVED_RECORDS, 1)
        packet.addParam(packets.CFG_VEHICLE_ON_STOP_MIN_PERIOD, 120) # seconds
        packet.addParam(packets.CFG_VEHICLE_ON_STOP_SEND_PERIOD, 180) # seconds
        # moving config
        packet.addParam(packets.CFG_VEHICLE_MOVING_MIN_SAVED_RECORDS, 1)
        packet.addParam(packets.CFG_VEHICLE_MOVING_MIN_PERIOD, 10) # seconds
        packet.addParam(packets.CFG_VEHICLE_MOVING_MIN_ANGLE, 10)
        packet.addParam(packets.CFG_VEHICLE_MOVING_MIN_DISTANCE, 500) # m
        packet.addParam(packets.CFG_VEHICLE_MOVING_SEND_PERIOD, 20) # seconds
        return packet

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        log.error('Teltonika::processCommandReadSettings NOT IMPLEMENTED')
        self.processCloseTask(task, None)

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        log.error('Teltonika::processCommandSetOption NOT IMPLEMENTED')
        self.processCloseTask(task, None)

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

    def test_getConfigurationSmsParts(self):
        h = self.handler
        configInitial = h.getInitiationConfig({
            "identifier": "0123456789012345",
            "host": "trx.maprox.net",
            "port": 21200
        })
        config = b'\x00\x92\x8c\x00\x1b\x03\xe8\x00\x01\x30\x03\xf2\x00\x01' +\
                 b'\x31\x03\xf3\x00\x02\x32\x30\x03\xf4\x00\x02\x31\x30\x03' +\
                 b'\xfc\x00\x01\x30\x04\x06\x00\x01\x30\x04\x07\x00\x01\x30' +\
                 b'\x04\x08\x00\x01\x30\x04\x09\x00\x01\x30\x04\x0a\x00\x01' +\
                 b'\x30\x04\x10\x00\x01\x30\x04\x11\x00\x01\x30\x04\x12\x00' +\
                 b'\x01\x30\x04\x13\x00\x01\x30\x04\x14\x00\x01\x30\x04\x1a' +\
                 b'\x00\x01\x30\x04\x1b\x00\x01\x30\x04\x1c\x00\x01\x30\x04' +\
                 b'\x1d\x00\x01\x30\x04\x1e\x00\x01\x30\x04\x24\x00\x01\x30' +\
                 b'\x04\x25\x00\x01\x30\x04\x26\x00\x01\x30\x04\x27\x00\x01' +\
                 b'\x30\x04\x28\x00\x01\x30\x0c\xbd\x00\x0c+37044444444'
        #config = h.getConfigurationPacket(configInitial).rawData
        parts = h.getConfigurationSmsParts(configInitial, config)
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), consts.SMS_BINARY_MAX_LENGTH)
        self.assertEqual(len(parts[1]), 32)
    
    def test_processData(self):
        h = self.handler
        data = b'\x00\x00\x00\x00\x00\x00\x02\xf1\x08\x19\x00\x00\x01<' +\
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
        data1 = b'\x00\x92\x8c\x00\x1b\x03\xe8\x00\x01\x30\x03\xf2\x00\x01' + \
               b'\x31\x03\xf3\x00\x02\x32\x30\x03\xf4\x00\x02\x31\x30\x03' + \
               b'\xfc\x00\x01\x30\x04\x06\x00\x01\x30\x04\x07\x00\x01\x30' + \
               b'\x04\x08\x00\x01\x30\x04\x09\x00\x01\x30\x04\x0a\x00\x01' + \
               b'\x30\x04\x10\x00\x01\x30\x04\x11\x00\x01\x30\x04\x12\x00' + \
               b'\x01\x30\x04\x13\x00\x01\x30\x04\x14\x00\x01\x30\x04\x1a' +\
               b'\x00\x01\x30\x04\x1b\x00\x01\x30\x04\x1c\x00\x01\x30\x04' +\
               b'\x1d\x00\x01\x30\x04\x1e\x00\x01\x30\x04\x24\x00\x01\x30' +\
               b'\x04\x25\x00\x01\x30\x04\x26\x00\x01\x30\x04\x27\x00\x01' +\
               b'\x30\x04\x28\x00\x01\x30\x0c\xbd\x00\x0c+37044444444'
        h.processData(data)
        #print("!!!!!!!!!!!Teltonika processData:::!!!!!!!!!!")
        #print(h.getStore())
        #print(h.getStore().stored_protocol_packets[0].AvlDataArray.items[0]._params['longitude'])
        
        stored_protocol_packets = h.getStore().stored_protocol_packets
        packet_avl_data_array = stored_protocol_packets[0].AvlDataArray
        packet_params =  packet_avl_data_array.items[0]._params
        
        #print("Packet parameters:")
        #print(packet_params)
        
        self.assertEqual(len(packet_avl_data_array.items), 25)
        self.assertEqual(packet_avl_data_array.items[0].ioElement, {
            'eventIoId': 0,
            'items': []
        })
        
        self.assertEqual(packet_params['altitude'], 291)
        self.assertEqual(packet_params['satellitescount'], 7)
        
        #print(packet_avl_data_array.items[0].ioElement)
        
        
        #print (h.getStore().get_stored_packets())
