# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset packets
@copyright 2013, Maprox LLC
'''

import time
import socket
from datetime import datetime
from struct import unpack, pack
import lib.bits as bits
import lib.crc16 as crc16
from lib.packets import *

# ---------------------------------------------------------------------------

class NavisetBase(BasePacket):
    """
     Base class for naviset packet.
    """

    # protected properties
    _fmtChecksum = '<H' # checksum format

    def calculateChecksum(self):
        """
         Calculates CRC (CRC-16 Modbus)
         @param buffer: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        data = (self._head or b'') + (self._body or b'')
        return crc16.Crc16.calcBinaryString(data, crc16.INITIAL_MODBUS)

# ---------------------------------------------------------------------------

class NavisetPacket(NavisetBase):
    """
     Default naviset protocol packet
    """

    # protected properties
    _fmtHeader = None   # header format
    _fmtLength = '<H'   # packet length format

    def _parseLength(self):
        # read header and length
        head = unpack(self._fmtLength, self._head)[0]
        head = bits.bitClear(head, 15)
        head = bits.bitClear(head, 14)
        #head = bits.bitClear(head, 13)
        #head = bits.bitClear(head, 12)
        self._length = head
        self._header = head >> 14

    def _buildHead(self):
        """
         Builds rawData from object variables
         @protected
        """
        length = len(self._body)
        data = length + (self._header << 14)
        return pack(self._fmtLength, data)

# ---------------------------------------------------------------------------

class PacketNumbered(NavisetPacket):
    """
      Packet of naviset messaging protocol with device number in body
    """

    # private properties
    __deviceNumber = 0

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketNumbered, self)._parseBody()
        self.__deviceNumber = unpack("<H", self._body[:2])[0]

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = b''
        result += pack('<H', self.__deviceNumber)
        return result

    @property
    def deviceNumber(self):
        if self._rebuild: self._build()
        return self.__deviceNumber

    @deviceNumber.setter
    def deviceNumber(self, value):
        if (0 <= value <= 0xFFFF):
            self.__deviceNumber = value
            self._rebuild = True

# ---------------------------------------------------------------------------

class PacketHead(PacketNumbered):
    """
      Head packet of naviset messaging protocol
    """
    # private properties
    __deviceImei = 0
    __protocolVersion = None

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketHead, self)._parseBody()
        lengthOfIMEI = 15
        self.__deviceImei = self._body[2:2 + lengthOfIMEI].decode()
        self.__protocolVersion = unpack("<B", self._body[-1:])[0]

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketHead, self)._buildBody()
        result += self.__deviceImei.encode()
        result += pack('<B', self.__protocolVersion)
        return result

    @property
    def deviceImei(self):
        if self._rebuild: self._build()
        return self.__deviceImei

    @deviceImei.setter
    def deviceImei(self, value):
        if (len(value) == 15):
            self.__deviceImei = str(value)
            self._rebuild = True

    @property
    def protocolVersion(self):
        if self._rebuild: self._build()
        return self.__protocolVersion

    @protocolVersion.setter
    def protocolVersion(self, value):
        if (0 <= value <= 0xFF):
            self.__protocolVersion = value
            self._rebuild = True

# ---------------------------------------------------------------------------

class PacketData(PacketNumbered):
    """
      Data packet of naviset messaging protocol
    """
    # private properties
    __dataStructure = 0
    __itemsData = None
    __items = None

    def __init__(self, data = None):
        """
         Constructor
         @param data: Binary data of data packet
         @return: PacketData instance
        """
        self.__items = []
        super(PacketData, self).__init__(data)

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketData, self)._parseBody()
        self.__dataStructure = unpack('<H', self._body[2:4])[0]
        self.__itemsData = self._body[4:]
        self.__items = PacketDataItem.getDataItemsFromBuffer(
            self.__itemsData,
            self.__dataStructure
        )

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketData, self)._buildBody()
        result += pack('<H', self.__dataStructure)
        return result

    @property
    def items(self):
        return self.__items

# ---------------------------------------------------------------------------

class PacketDataItem:
    """
      Item of data packet of naviset messaging protocol
    """
    # private properties
    __rawData = None
    __rawDataTail = None
    __dataStructure = 0
    __number = 0
    __params = None
    __additional = 0

    def __init__(self, data = None, ds = 0):
        """
         Constructor
         @param data: Binary data for packet item
         @param ds: Data structure word
         @return: PacketDataItem instance
        """
        super(PacketDataItem, self).__init__()
        self.__rawData = data
        self.__dataStructure = ds
        self.__params = {}
        self.__parse()

    @classmethod
    def getAdditionalDataLength(cls, ds = None):
        """
         Returns length of additional data buffer
         according to ds parameter
         @param ds: Data structure definition (2 byte)
         @return: Size of additional data buffer in bytes
        """
        # exit if dataStructure is empty
        if (ds == None) or (ds == 0):
            return 0

        dsMap = {
             0: 1,
             1: 4,
             2: 1,
             3: 2,
             4: 4,
             5: 4,
             6: 4,
             7: 4,
             8: 4,
             9: 4,
            10: 6,
            11: 4,
            12: 4,
            13: 2,
            14: 4,
            15: 8
        }
        size = 0
        for key in dsMap:
            if bits.bitTest(ds, key):
                size += dsMap[key]
        return size

    @classmethod
    def getDataItemsFromBuffer(cls, data = None, ds = None):
        """
         Returns an array of PacketDataItem instances from data
         @param data: Input binary data
         @return: array of PacketDataItem instances (empty array if not found)
        """
        items = []
        while True:
            item = cls(data, ds)
            data = item.rawDataTail
            items.append(item)
            if data is None or len(data) == 0: break
        return items

    def convertCoordinate(self, coord):
        result = str(coord)
        result = result[:2] + '.' + result[2:]
        return float(result)

    def __parse(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        buffer = self.__rawData
        length = self.length
        if buffer == None: return
        if len(buffer) < length: return

        self.__number = unpack("<H", buffer[:2])[0]
        self.__params['time'] = datetime.utcfromtimestamp(
            unpack("<L", buffer[2:6])[0]) #- timedelta(hours=4)
        self.__params['satellitescount'] = unpack("<B", buffer[6:7])[0]
        self.__params['latitude'] = self.convertCoordinate(
            unpack("<L", buffer[7:11])[0])
        self.__params['longitude'] = self.convertCoordinate(
            unpack("<L", buffer[11:15])[0])
        self.__params['speed'] = unpack("<H", buffer[15:17])[0] / 10
        self.__params['azimuth'] = int(round(
            unpack("<H", buffer[17:19])[0] / 10))
        self.__params['altitude'] = unpack("<H", buffer[19:21])[0]
        self.__params['hdop'] = unpack("<B", buffer[21:22])[0] / 10
        self.__additional = buffer[22:length]

        # apply new data
        self.__rawDataTail = buffer[length:]
        self.__rawData = buffer[:length]

    @property
    def length(self):
        return 22 + self.getAdditionalDataLength(self.__dataStructure)

    @property
    def rawData(self):
        return self.__rawData

    @property
    def rawDataTail(self):
        return self.__rawDataTail

    @property
    def number(self):
        return self.__number

    @property
    def params(self):
        return self.__params

    @property
    def additional(self):
        return self.__additional

# ---------------------------------------------------------------------------

class PacketAnswer(NavisetPacket):
    """
      Data packet of naviset messaging protocol
    """

    # private properties
    _command = 0

    @property
    def command(self):
        if self._rebuild: self._build()
        return self._command

    @classmethod
    def getInstance(cls, data = None):
        CLASS = None
        if data:
            command = unpack('<B', data[2:3])[0]
            CLASS = getAnswerClassByNumber(command)
        return CLASS

# ---------------------------------------------------------------------------

class Command(NavisetBase):
    """
     A command packet
    """

    # protected properties
    _fmtHeader = '<H'   # header format
    _fmtLength = None   # packet length format

    _header = 2
    _number = 0

    @property
    def number(self):
        if self._rebuild: self._build()
        return self._number

    def __init__(self, params = None):
        """
         Initialize command with specific params
         @param params: dict
         @return:
        """
        super(Command, self).__init__()
        self.setParams(params)

    def setParams(self, params):
        """
         Set command params if needed.
         Override in child classes.
         @param params: dict
         @return:
        """
        self._rebuild = True

    def _parseHeader(self):
        # read header and command number
        unpacked = unpack('<BB', self._head)
        self._header = unpacked[0]
        self._number = unpacked[1]
        headerCode = 0x02
        if (self._header != headerCode):
            raise Exception('Incorrect command packet! ' +\
                            str(self._header) + ' (given) != ' +\
                            str(headerCode) + ' (must be)')

    def _buildHead(self):
        data = b''
        data += pack('<B', self._header)
        data += pack('<B', self._number)
        return data

# ---------------------------------------------------------------------------
# Simple commands
# ---------------------------------------------------------------------------

class CommandGetStatus(Command): _number = 0
class CommandGetImei(Command): _number = 1
class CommandGetRegisteredIButtons(Command): _number = 5
class CommandGetPhones(Command): _number = 7
class CommandGetTrackParams(Command): _number = 10
class CommandRemoveTrackFromBuffer(Command): _number = 16
class CommandRestart(Command): _number = 18

# ---------------------------------------------------------------------------

class CommandSetGprsParams(Command):
    """
     Change device GPRS params
    """
    _number = 4

    # private params
    __ip = ''
    __port = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.ip = params['ip'] or ''
        self.port = params['port'] or 0

    @property
    def ip(self):
        if self._rebuild: self._build()
        return self.__ip

    @ip.setter
    def ip(self, value):
        self.__ip = str(value)
        self._rebuild = True

    @property
    def port(self):
        if self._rebuild: self._build()
        return self.__port

    @port.setter
    def port(self, value):
        if (0 <= value <= 0xFFFF):
            self.__port = value
            self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += socket.inet_aton(self.__ip)
        data += pack('<H', self.__port)
        return data

# ---------------------------------------------------------------------------

IMAGE_RESOLUTION_80x64 = 0
IMAGE_RESOLUTION_160x128 = 1
IMAGE_RESOLUTION_320x240 = 2
IMAGE_RESOLUTION_640x480 = 3
IMAGE_PACKET_CONFIRM_OK = 16
IMAGE_PACKET_CONFIRM_CORRUPT = 32

class CommandGetImage(Command):
    """
     Command for image receiving/confirmation
    """
    _number = 20

    # private params
    __type = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.type = params['type'] or 0

    @property
    def type(self):
        if self._rebuild: self._build()
        return self.__type

    @type.setter
    def type(self, value):
        self.__type = str(value)
        self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__type))
        return data

# ---------------------------------------------------------------------------

IMAGE_ANSWER_CODE_SIZE = 0
IMAGE_ANSWER_CODE_DATA = 1
IMAGE_ANSWER_CODE_CAMERA_NOT_FOUND = 2
IMAGE_ANSWER_CODE_CAMERA_IS_BUSY = 3

class PacketAnswerCommandGetImage(PacketAnswer):
    """
     Answer on CommandGetImage
    """
    _command = 20

    __code = 0
    __imageSize = 0
    __chunkNumber = 0
    __chunkData = None

    @property
    def code(self):
        if self._rebuild: self._build()
        return self.__code

    @property
    def imageSize(self):
        if self._rebuild: self._build()
        return self.__imageSize

    @property
    def chunkNumber(self):
        if self._rebuild: self._build()
        return self.__chunkNumber

    @property
    def chunkData(self):
        if self._rebuild: self._build()
        return self.__chunkData

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketAnswerCommandGetImage, self)._parseBody()
        buffer = self._body
        self._command = unpack('<B', buffer[:1])[0]
        self.__code = unpack('<B', buffer[1:2])[0]
        if self.__code == IMAGE_ANSWER_CODE_SIZE:
            b, w = unpack('<HB', buffer[2:5])
            self.__imageSize = b | (w << 16)
        elif self.__code == IMAGE_ANSWER_CODE_DATA:
            self.__chunkNumber = unpack('<B', buffer[2:3])[0]
            chunkLength = unpack('<H', buffer[3:5])[0]
            self.__chunkData = buffer[5:5 + chunkLength]
            if len(self.__chunkData) != chunkLength:
                raise Exception('Incorrect image chunk length! ' +\
                    str(len(self.__chunkData)) + ' (given) != ' +\
                    str(chunkLength) + ' (must be)')

# ---------------------------------------------------------------------------

class PacketFactory:
    """
     Packet factory
    """

    @classmethod
    def getPacketsFromBuffer(cls, data = None):
        """
         Returns an array of BasePacket instances from data
         @param data: Input binary data
         @return: array of BasePacket instances (empty array if no packet found)
        """
        packets = []
        if not data: return packets
        while True:
            packet = cls.getInstance(data)
            data = packet.rawDataTail
            packets.append(packet)
            if (len(data) == 0): break
        return packets

    @classmethod
    def getClass(cls, number):
        """
         Returns a tag class by number
        """
        classes = {
            0: PacketHead,
            1: PacketData,
            2: PacketAnswer
        }
        if (not (number in classes)):
            return None
        return classes[number]

    @classmethod
    def getInstance(cls, data = None):
        """
          Returns a tag instance by its number
        """
        if data == None: return

        # read header and length
        length = unpack("<H", data[:2])[0]
        number = length >> 14

        CLASS = cls.getClass(number)
        if not CLASS:
            raise Exception('Packet %s is not found' % number)
        if issubclass(CLASS, PacketAnswer):
            CLASS = PacketAnswer.getInstance(data)
        if not CLASS:
            raise Exception('Class for %s is not found' % data)
        return CLASS(data)

import inspect
import sys

def getAnswerClassByNumber(number):
    """
     Returns command class by its number
     @param number: int Number of the command
     @return: Command class
    """
    for name, cls in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(cls) and \
            issubclass(cls, PacketAnswer) and\
                cls._command == number:
                    return cls
    return None


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_headPacket(self):
        packet = PacketFactory.getInstance(
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9')
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(isinstance(packet, PacketData), False)
        self.assertEqual(packet.header, 0)
        self.assertEqual(packet.length, 18)
        self.assertEqual(packet.body, b'\x01\x00012896001609129\x06')
        self.assertEqual(packet.checksum, 47519)

    def test_setPacketBody(self):
        packet = PacketFactory.getInstance(
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9')
        self.assertEqual(packet.length, 18)
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(packet.checksum, 47519)
        packet.body = b'\x22\x00012896001609129\x05'
        self.assertEqual(packet.length, 18)
        self.assertEqual(packet.deviceNumber, 34)
        self.assertEqual(packet.deviceImei, '012896001609129')
        self.assertEqual(packet.protocolVersion, 5)
        self.assertEqual(packet.rawData, b'\x12\x00\x22\x00012896001609129\x05$6')
        self.assertEqual(packet.checksum, 13860)

    def test_packetTail(self):
        packets = PacketFactory.getPacketsFromBuffer(
            b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9' +
            b'\x12\x00\x22\x00012896001609129\x05$6')
        self.assertEqual(len(packets), 2)

    def test_dataPacket(self):
        packets = PacketFactory.getPacketsFromBuffer(
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
        self.assertEqual(len(packets), 1)
        packet = packets[0]
        self.assertEqual(isinstance(packet, PacketData), True)
        self.assertEqual(len(packet.items), 12)
        packetItem = packet.items[3]
        self.assertEqual(isinstance(packetItem, PacketDataItem), True)
        self.assertEqual(packetItem.params['speed'], 0.0)
        self.assertEqual(packetItem.params['latitude'], 53.243104)
        self.assertEqual(packetItem.params['longitude'], 50.1834)
        self.assertEqual(packetItem.params['satellitescount'], 16)
        self.assertEqual(packetItem.params['time'].
            strftime('%Y-%m-%dT%H:%M:%S.%f'), '2013-04-04T03:22:34.000000')
        packetItem2 = packet.items[6]
        self.assertEqual(packetItem2.params['speed'], 0)
        self.assertEqual(packetItem2.params['satellitescount'], 16)
        self.assertEqual(packetItem2.number, 10606)
        self.assertEqual(packetItem2.additional, b'')
        #self.assertEqual(packetItem2.sensor, b'')

    def test_simpleCommandsPacket(self):
        cmd = CommandGetStatus()
        self.assertEqual(cmd.number, 0)
        self.assertEqual(cmd.rawData, b'\x02\x00\x00\xd0')

        cmd = CommandGetRegisteredIButtons()
        self.assertEqual(cmd.number, 5)
        self.assertEqual(cmd.checksum, 54208)
        self.assertEqual(cmd.rawData, b'\x02\x05\xc0\xd3')

    def test_gprsCommandsPacket(self):
        cmd = CommandSetGprsParams({
            "ip": '127.0.0.1',
            "port": 20200
        })
        self.assertEqual(cmd.number, 4)
        self.assertEqual(cmd.checksum, 10512)
        self.assertEqual(cmd.rawData, b'\x02\x04\x7f\x00\x00\x01\xe8N\x10)')
        # let's change port and ip
        cmd.port = 20201
        cmd.ip = '212.10.222.10'
        self.assertEqual(cmd.rawData, b'\x02\x04\xd4\n\xde\n\xe9N\xdb\x89')

    def test_getImageCommandsPacket(self):
        cmd = CommandGetImage({
            'type': IMAGE_RESOLUTION_640x480
        })
        self.assertEqual(cmd.number, 20)
        self.assertEqual(cmd.rawData, b'\x02\x14\x03\x9f\x01')

        cmd.type = IMAGE_PACKET_CONFIRM_OK
        self.assertEqual(cmd.rawData, b'\x02\x14\x10\xde\xcc')

    def test_commandAnswerGetImage(self):
        data = b'\x05\x80\x14\x00\xb1\x46\x00\x03\x84'
        packets = PacketFactory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertIsInstance(packet, PacketAnswerCommandGetImage)
        self.assertEqual(packet.command, 20)
        self.assertEqual(packet.code, 0)
        self.assertEqual(packet.imageSize, 18097)

    def test_commandAnswerGetImageChunk(self):
        data = b'\xff\x81\x14\x01\x00\xfa\x01\xff\xd8\xff\xdb\x00\x84' + \
               b'\x00\x13\r\x0e\x10\x0e\x0c\x13\x10\x0f\x10\x15\x14\x13' + \
               b'\x16\x1c/\x1e\x1c\x1a\x1a\x1c9)+"/D<GFC<B@KTl[KPfQ@B^\x80' + \
               b'_fosyzyIZ\x84\x8e\x83u\x8dlvyt\x01\x14\x15\x15\x1c\x19' +\
               b'\x1c7\x1e\x1e7tMBMtttttttttttttttttttttttttttttttttttt' +\
               b'tttttttttttttt\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03' +\
               b'\x01!\x00\x02\x11\x01\x03\x11\x01\xff\xdd\x00\x04\x00(' +\
               b'\xff\xc4\x01\xa2\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06' +\
               b'\x07\x08\t\n\x0b\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05' +\
               b'\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12' +\
               b'!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R' +\
               b'\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CD' +\
               b'EFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89' +\
               b'\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5' +\
               b'\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba' +\
               b'\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6' +\
               b'\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea' +\
               b'\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\x01\x00\x03\x01' +\
               b'\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00' +\
               b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x11\x00\x02\x01' +\
               b'\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01' +\
               b'\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B' +\
               b'\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17' +\
               b'\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvw\xc1\xb0'
        packets = PacketFactory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet.chunkNumber, 0)
        self.assertEqual(len(packet.chunkData), 506)