# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Ime packets
@copyright 2013, Maprox LLC
"""

import binascii
import re
import inspect
import sys
from lib.crc16 import Crc16
from lib.packets import *
from lib.geo import Geo
from lib.factory import AbstractPacketFactory

# ---------------------------------------------------------------------------

class ImeBase(BasePacket):
    """
     Base packet for Ime protocol
     From server to tracker:
       @@<L(2b)><ID(7b)><command(2b)><parameter><checksum(2b)>\r\n
     From tracker to server:
       $$<L(2b)><ID(7b)><command(2b)><data><checksum(2b)>\r\n
    """
    _fmtHeader = '>H'   # header format
    _fmtFooter = '>H'   # header format
    _fmtLength = '>H'   # length format
    _fmtChecksum = '>H' # checksum format
    _header = None      # prefix of the packet (can be $$ or @@)
    _footer = 0x0D0A    # $$ - prefix of the packet (can be $$ or @@)
    _data = None        # packet internal data

    # private properties
    __deviceImei = 0
    _command = 0        # expected command number

    def _parseLength(self):
        """
         Parses packet length data.
         If return None, then offset is shifted to calcsize(self._fmtLength)
         otherwise to the returned value
         @return:
        """
        # we need to subtract 8 bytes, because protocol
        # also counts header, length bytes, prefix length and checksum
        self._length -= 8

    def _parseBody(self):
        """
         Parses header data.
         If return None, then offset is shifted to calcsize(self._fmtHeader)
         otherwise to the returned value
         @return:
        """
        imeiChunk = binascii.hexlify(self._body[:7]).decode()
        self.__deviceImei = re.sub('[^\d]', '', imeiChunk)
        self._command = unpack('>H', self._body[7:9])[0]
        self._data = self._body[9:]
        return None

    # public link to checksum calculation function
    # (CRC-16 CCITT 0xFFFF by default)
    fnChecksum = Crc16.calcCCITT
    def calculateChecksum(self):
        """
         Calculates CRC
         @return: True if buffer crc equals to supplied crc value, else False
        """
        data = (self._head or b'') + (self._body or b'')
        return self.fnChecksum(data)

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        deviceId = self.__deviceImei.encode()
        while len(deviceId) < 14: deviceId += b'F'
        data += binascii.unhexlify(deviceId)
        data += pack('>H', self._command)
        return data

    def _buildCalculateLength(self):
        """
         Calculates length of the packet
         @return: int
        """
        self._length = 0
        if self._body is not None:
            self._length = len(self._body)
        return self._length + 8

    @property
    def deviceImei(self):
        if self._rebuild: self._build()
        return self.__deviceImei

    @deviceImei.setter
    def deviceImei(self, value):
        self.__deviceImei = str(value)
        self._rebuild = True

    @property
    def command(self):
        if self._rebuild: self._build()
        return self._command

    @command.setter
    def command(self, value):
        self._command = value
        self._rebuild = True

    @property
    def data(self):
        if self._rebuild: self._build()
        return self._data

# ---------------------------------------------------------------------------
# COMMANDS LIST

CMD_LOGIN = 0x5000
CMD_LOGIN_CONFIRMATION = 0x4000
CMD_TRACK_ON_DEMAND = 0x4101
CMD_TRACK_BY_INTERVAL = 0x4102
CMD_AUTHORIZATION = 0x4103
CMD_SPEEDING_ALARM = 0x4105
CMD_MOVEMENT_ALARM = 0x4106
CMD_EXTENDED_SETTINGS = 0x4108
CMD_INITIALIZATION = 0x4110
CMD_SLEEP_MODE = 0x4113
CMD_OUTPUT_CONTROL_CONDITIONAL = 0x4114 # OR 0x5114
CMD_OUTPUT_CONTROL_IMMEDIATE = 0x4115
CMD_TRIGGERED_ALARMS = 0x4116
CMD_POWER_DOWN = 0x4126
CMD_LISTEN_IN_VOICE_MONITORING = 0x4130
CMD_LOG_BY_INTERVAL = 0x4131
CMD_TIME_ZONE = 0x4132
CMD_SET_SENSITIVITY_OF_TREMBLE_SENSOR = 0x4135
CMD_HEADING_CHANGE_REPORT = 0x4136
CMD_SET_GPS_ANTENNA_CUT_ALARM = 0x4150 # FOR VT400 ONLY
CMD_SET_GPRS_PARAMETERS = 0x4155
CMD_SET_GEOFENCE_ALARM = 0x4302
CMD_TRACK_BY_DISTANCE = 0x4303
CMD_DELETE_MILEAGE = 0x4351
CMD_REBOOT_GPS = 0x4902
CMD_HEARTBEAT = 0x5199
CMD_CLEAR_MESSAGE_QUEUE = 0x5503
CMD_GET_SN_AND_IMEI = 0x9001
CMD_READ_INTERVAL = 0x9002
CMD_READ_AUTHORIZATION = 0x9003
CMD_READ_LOGGED_DATA = 0x9016
CMD_ALARMS = 0x9999

# ---------------------------------------------------------------------------
# ANSWERS LIST

ANSWER_DATA = 0x9955

# ---------------------------------------------------------------------------

class ImePacket(ImeBase):
    """
     Base packet for Ime protocol
    """
    _header = 0x2424    # $$ - prefix of the packet (can be $$ or @@)

# ---------------------------------------------------------------------------

class ImePacketLogin(ImePacket):
    """
     Data packet for Ime protocol (coordinates from device)
    """
    _command = CMD_LOGIN

# ---------------------------------------------------------------------------

class ImePacketData(ImePacket):
    """
     Data packet for Ime protocol (coordinates from device)
    """
    _command = ANSWER_DATA

    # private properties
    __params = None

    def _parseBody(self):
        """
         Parses body of the packet
         @protected
        """
        super(ImePacketData, self)._parseBody()
        self.__params = {}
        sensors = {}
        parts = self._data.decode().split("|")
        gprmc = parts[0].split(',')
        # lets get packet time
        self.__params['time'] = datetime.strptime(
            gprmc[8] + ',' + gprmc[0], '%d%m%y,%H%M%S.%f')
        # and coordinates
        sensors['latitude'] = Geo.getLatitude(gprmc[2] + gprmc[3])
        sensors['longitude'] = Geo.getLongitude(gprmc[4] + gprmc[5])
        # and other params
        sensors['speed'] = float(gprmc[6] or 0) * 1.85200
        sensors['azimuth'] = int(float(gprmc[7] or 0))
        sensors['sat_count'] = 10 # fake sat_count
        sensors['hdop'] = float(parts[1] or 0)
        sensors['altitude'] = int(float(parts[2] or 0))

        self.__params['sensors'] = sensors.copy()
        # old fashioned params
        for key in ['latitude', 'longitude', 'speed',
                    'altitude', 'azimuth', 'hdop']:
            if key in sensors:
                self.__params[key] = sensors[key]
        if 'sat_count' in sensors:
            self.__params['satellitescount'] = sensors['sat_count']

    @property
    def params(self):
        if self._rebuild: self._build()
        return self.__params

# ---------------------------------------------------------------------------

# noinspection PyCallingNonCallable
class PacketFactory(AbstractPacketFactory):
    """
     Packet factory
    """
    def getInstance(self, data = None):
        """
          Returns a tag instance by its number
        """
        if data is None: return

        # read packetId
        packetPrefix = data[:2]
        if packetPrefix != b'$$':
            raise Exception('Packet %s is not found' %
                binascii.hexlify(packetPrefix).decode())

        packet = ImePacket(data)
        for name, cls in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(cls) and issubclass(cls, ImePacket):
                if cls._command == packet.command:
                    return cls(data)

        return None

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
from datetime import datetime
class TestCase(unittest.TestCase):

    def setUp(self):
        ImeBase.fnChecksum = Crc16.calcCCITT
        ImeBase._fmtChecksum = '>H'
        self.factory = PacketFactory()
        pass

    def test_checkLoginPacket(self):
        packets = self.factory.getPacketsFromBuffer(
            b'\x24\x24\x00\x11\x13\x61\x23\x45\x67\x8f'
            b'\xff\x50\x00\x05\xd8\x0d\x0a'
        )
        packet = packets[0]
        self.assertEqual(packet.deviceImei, '13612345678')
        self.assertEqual(packet.command, CMD_LOGIN)

    def test_checkDataPacket(self):
        packets = self.factory.getPacketsFromBuffer(
            b'\x24\x24\x00\x60\x12\x34\x56\xFF\xFF\xFF\xFF\x99'
            b'\x55\x30\x33\x35\x36\x34\x34\x2E\x30\x30\x30\x2C'
            b'\x41\x2C\x32\x32\x33\x32\x2E\x36\x30\x38\x33\x2C'
            b'\x4E\x2C\x31\x31\x34\x30\x34\x2E\x38\x31\x33\x37'
            b'\x2C\x45\x2C\x30\x2E\x30\x30\x2C\x2C\x30\x31\x30'
            b'\x38\x30\x39\x2C\x2C\x2A\x31\x43\x7C\x31\x31\x2E'
            b'\x35\x7C\x31\x39\x34\x7C\x30\x30\x30\x30\x7C\x30'
            b'\x30\x30\x30\x2C\x30\x30\x30\x30\x69\x62\x0D\x0A'
        )
        p = packets[0]
        self.assertEqual(p.deviceImei, '123456')
        self.assertEqual(p.command, ANSWER_DATA)
        self.assertIsInstance(p, ImePacketData)

        self.assertEqual(p.params['time'], datetime(2009, 8, 1, 3, 56, 44))
        self.assertAlmostEqual(p.params['latitude'], 22.54347166)
        self.assertAlmostEqual(p.params['longitude'], 114.080228333)
        sensors = p.params['sensors']
        self.assertEqual(sensors['sat_count'], 10)
        self.assertEqual(sensors['speed'], 0.00)
        self.assertEqual(sensors['altitude'], 194)
        self.assertEqual(sensors['azimuth'], 0)

if __name__ == '__main__':
    unittest.main()