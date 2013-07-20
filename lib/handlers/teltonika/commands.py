# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Teltonika commands
@copyright 2013, Maprox LLC
"""

import os
import binascii

import lib.consts as consts
from lib.commands import *
from lib.factory import AbstractCommandFactory
import lib.handlers.teltonika.packets as packets
from kernel.dbmanager import db

# ---------------------------------------------------------------------------

class TeltonkaCommand(AbstractCommand):
    """
     Teltonka command packet
    """
    pass

# ---------------------------------------------------------------------------

class TeltonkaCommandConfigure(TeltonkaCommand, AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = True
    """ False if protocol doesn't support dns hostname (only ip-address) """

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
        packet.addParam(packets.CFG_TARGET_SERVER_IP_ADDRESS, config['host'])
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
        buffer += packString(data['device']['login'])
        buffer += packString(data['device']['password'])
        buffer += packString(data['host'])
        buffer += pack('>H', data['port'])
        buffer += packString(data['gprs']['apn'])
        buffer += packString(data['gprs']['username'])
        buffer += packString(data['gprs']['password'])
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
        header += packString(data['device']['login'])
        header += packString(data['device']['password'])
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
         Creates push sms data (1st config method) - WE USE THIS!
         @param config:
         @return:
        """
        # create config packet and save it to the database
        packet = self.getConfigurationPacket(config)
        current_db = db.get(config['identifier'])
        current_db.set('config', packet.rawData)
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
        # create push-sms for configuration
        parts = self.getConfigurationSmsParts(config, packet.rawData)
        data = []
        for buffer in parts:
            data.append({
                'message': binascii.hexlify(buffer).decode(),
                'bin': consts.SMS_BINARY_HEX_STRING
            })
        return data

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        if transport == "sms":
            # We use first variant of configuration:
            # First step is to send push sms to the device,
            # in which we tell the server ip to get configuration from.
            # Then a device connects to the server and we send
            # configuration to it via tcp connection.
            return self.getPushSmsData(self._initiationConfig)
        else:
            return super(TeltonkaCommandConfigure, self).getData(transport)

# ---------------------------------------------------------------------------

class CommandFactory(AbstractCommandFactory):
    """
     Command factory
    """
    module = __name__

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        self.factory = CommandFactory()

    def test_packetData(self):
        cmd = self.factory.getInstance({
            'command': 'configure',
            'params': {
                "identifier": "0123456789012345",
                "host": "trx.maprox.net",
                "port": 21202
            }
        })
        self.assertEqual(cmd.getData('sms'), [{
            'bin': 2,
            'push': True,
            'message': '06050407d1000000000e7472782e6' + \
                       'd6170726f782e6e657452d2000000'
        }])