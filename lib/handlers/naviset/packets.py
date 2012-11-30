# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset packets
@copyright 2012, Maprox LLC
'''

import time
from datetime import datetime, timedelta
from struct import unpack, pack
import lib.bits as bits
import lib.crc16 as crc16

# ---------------------------------------------------------------------------

class Packet(object):
    """
     Default naviset protocol packet
    """

    # private properties
    __header = 0
    __length = 0
    __rawData = None
    __rawDataTail = None
    __body = None
    __crc = 0

    # protected properties
    _encoding = "utf-8" # string encoding
    _rebuild = True     # flag to rebuild rawData

    def __init__(self, data = None):
        """
         Constructor
         @param data: Input binary data
        """
        self.rawData = data

    @property
    def header(self):
        if self._rebuild: self.__build()
        return self.__header

    @header.setter
    def header(self, value):
        if (value < 4):
            self.__header = value
            self._rebuild = True

    @property
    def length(self):
        if self._rebuild: self.__build()
        return self.__length

    @property
    def rawData(self):
        if self._rebuild: self.__build()
        return self.__rawData

    @rawData.setter
    def rawData(self, value):
        self._rebuild = False
        self.__rawData = value
        self.__parse()

    @property
    def rawDataTail(self):
        return self.__rawDataTail

    @property
    def body(self):
        if self._rebuild: self.__build()
        return self.__body

    @body.setter
    def body(self, value):
        self.__body = value
        self._parseBody(value)
        self._rebuild = True

    @property
    def crc(self):
        if self._rebuild: self.__build()
        return self.__crc

    def __parse(self):
        """
         Parses rawData
        """
        buffer = self.__rawData
        if buffer == None: return

        # read header and length
        length = unpack("<H", buffer[:2])[0]
        header = length >> 14
        length = bits.bitClear(length, 15)
        length = bits.bitClear(length, 14)

        # now let's read packet data
        # but before this, check body length
        body = buffer[2:length + 2]
        if len(body) != length:
            raise Exception('Body length Is incorrect! ' +
                str(length) + ' (said) != ' + str(len(body)) + ' (real)')

        crc = unpack("<H", buffer[length + 2:length + 4])[0]
        crc_data = buffer[:length + 2]
        crc_calculated = self.getCrc(crc_data)
        if (crc != crc_calculated):
            raise Exception('Crc Is incorrect! ' +
                str(crc) + ' (said) != ' + str(crc_calculated) + ' (real)')

        # apply new data
        self.__rawDataTail = buffer[length + 4:]
        self.__rawData = buffer[:length + 4]
        self.__header = header
        self.__length = length
        self.__body = body
        self.__crc = crc

        # parse packet body
        self._parseBody(body)

    def __build(self):
        """
         Builds rawData from object variables
         @protected
        """
        self.__body = self._buildBody()
        self._rebuild = False
        self.__length = len(self.__body)
        head = self.__length + (self.__header << 14)

        self.__rawData = pack("<H", head)
        self.__rawData += self.__body
        self.__crc = crc16.Crc16.calcBinaryString(
          self.__rawData,
          crc16.INITIAL_MODBUS
        )
        self.__rawData += pack("<H", self.__crc)

    def _parseBody(self, data):
        """
         Parses body of the packet
        """
        pass

    def _buildBody(self):
        """
         Parses body of the packet
        """
        return self.__body

    @classmethod
    def getCrc(cls, buffer):
        """
         Calculates CRC (CRC-16 Modbus)
         @param buffer: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        return crc16.Crc16.calcBinaryString(
            buffer, crc16.INITIAL_MODBUS)

# ---------------------------------------------------------------------------

class PacketNumbered(Packet):
    """
      Packet of naviset messaging protocol with device number in body
    """

    # private properties
    __deviceNumber = 0

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketNumbered, self)._parseBody(body)
        self.__deviceNumber = unpack("<H", body[:2])[0]

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
        if self._rebuild: self.__build()
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
    __deviceIMEI = 0
    __protocolVersion = None

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketHead, self)._parseBody(body)
        lengthOfIMEI = 15
        self.__deviceIMEI = body[2:2 + lengthOfIMEI].decode(self._encoding)
        self.__protocolVersion = unpack("<B", body[-1:])[0]

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketHead, self)._buildBody()
        result += self.__deviceIMEI.encode(self._encoding)
        result += pack('<B', self.__protocolVersion)
        return result

    @property
    def deviceIMEI(self):
        if self._rebuild: self.__build()
        return self.__deviceIMEI

    @deviceIMEI.setter
    def deviceIMEI(self, value):
        if (len(value) == 15):
            self.__deviceIMEI = str(value)
            self._rebuild = True

    @property
    def protocolVersion(self):
        if self._rebuild: self.__build()
        return self.__protocolVersion

    @protocolVersion.setter
    def protocolVersion(self, value):
        if (0 <= value <= 0xFF):
            self.__protocolVersion = value
            self._rebuild = True

# ---------------------------------------------------------------------------

class Command():
    """
     A command packet
    """

    CMD_GET_STATUS = 0
    CMD_GET_IMEI = 1
    CMD_CHANGE_NUMBER = 2
    CMD_CHANGE_PASSWORD = 3

# ---------------------------------------------------------------------------

class PacketAnswer(Packet):
    """
      Data packet of naviset messaging protocol
    """

    # private properties
    __command = 0

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketAnswer, self)._parseBody(body)
        self.__command = Command.CMD_GET_STATUS

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketAnswer, self)._buildBody()
        result += pack('<B', self.__command)
        return result

    @property
    def command(self):
        if self._rebuild: self.__build()
        return self.__command

    @command.setter
    def command(self, value):
        pass

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

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketData, self)._parseBody(body)
        self.__dataStructure = unpack('<H', body[2:4])[0]
        self.__itemsData = body[4:]
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
            if len(data) == 0: break
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
        self.__params['time'] = datetime.fromtimestamp(
            unpack("<L", buffer[2:6])[0]) - timedelta(hours=4)
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
        return CLASS(data)

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
        self.assertEqual(packet.crc, 47519)

    def test_setPacketBody(self):
        packet = PacketFactory.getInstance(
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9')
        self.assertEqual(packet.length, 18)
        self.assertEqual(isinstance(packet, PacketHead), True)
        packet.body = b'\x22\x00012896001609129\x05'
        self.assertEqual(packet.length, 18)
        self.assertEqual(packet.deviceNumber, 34)
        self.assertEqual(packet.deviceIMEI, '012896001609129')
        self.assertEqual(packet.protocolVersion, 5)
        self.assertEqual(packet.rawData, b'\x12\x00\x22\x00012896001609129\x05$6')

    def test_packetTail(self):
        packets = PacketFactory.getPacketsFromBuffer(
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9' +
          b'\x12\x00\x22\x00012896001609129\x05$6')
        self.assertEqual(len(packets), 2)

    def test_dataPacket(self):
        packets = PacketFactory.getPacketsFromBuffer(
          b'\xe2C\x01\x00\x00\x00\x00\x00s\x01\xaaP\x10HfR\x034\x91=\x02' +
          b'\x00\x00\x00\x00\x00\x00\xff\x01\x00s\x01\xaaP\x10HfR\x034\x91' +
          b'=\x02\x00\x00\x00\x00\x00\x00\xff\x02\x00\x8f\x02\xaaP\x068fR' +
          b'\x03\x18\x91=\x02\x01\x00\x00\x00\xb0\x00\x1c\x03\x00\xae\x02' +
          b'\xaaP\x07\xfceR\x03t\x91=\x02\x03\x00\x00\x00\x9c\x00\x1a\x04' +
          b'\x00\xbd\x02\xaaP\x07\xfceR\x03\x84\x91=\x02\x00\x007\x04\xa3' +
          b'\x00\x1a\x05\x00\'\x03\xaaP\t\xfceR\x03\x84\x91=\x02\x00\x00\x00' +
          b'\x00\xa3\x00\x0b\x06\x00\xa0\x03\xaaP\t\xfceR\x03\x84\x91=\x02' +
          b'\x00\x00\x00\x00\xa2\x00\r\x07\x00\x19\x04\xaaP\n\xfceR\x03\x84' +
          b'\x91=\x02\x00\x00X\n\xa0\x00\x0b\x08\x00\x92\x04\xaaP\x0b\xfceR' +
          b'\x03\x84\x91=\x02\x00\x00\x00\x00\x9c\x00\n\t\x00\x0b\x05\xaaP' +
          b'\n\xfceR\x03\x84\x91=\x02\x00\x00+\n\x9a\x00\n\n\x00\x84\x05\xaa' +
          b'P\x0c\xfceR\x03\x84\x91=\x02\x00\x00\xb9\t\x99\x00\t\x0b\x00\xfd' +
          b'\x05\xaaP\x0b\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x98\x00\n' +
          b'\x0c\x00v\x06\xaaP\t\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x99' +
          b'\x00\x0b\r\x00\xef\x06\xaaP\x0c\xfceR\x03\x84\x91=\x02\x00\x00' +
          b'\xe4\x08\x98\x00\x08\x0e\x00h\x07\xaaP\t\xfceR\x03\x84\x91=\x02' +
          b'\x00\x00H\n\x98\x00\n\x0f\x00\xe1\x07\xaaP\x0c\xfceR\x03\x84\x91' +
          b'=\x02\x00\x008\x0c\x98\x00\x08\x10\x00Z\x08\xaaP\x0b\xfceR\x03' +
          b'\x84\x91=\x02\x00\x00\x00\x00\x98\x00\n\x11\x00\xd3\x08\xaaP' +
          b'\x0c\xfceR\x03\x84\x91=\x02\x00\x00\xe5\t\x98\x00\t\x12\x00L\t' +
          b'\xaaP\x0c\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x93\x00\x08\x13' +
          b'\x00\xc5\t\xaaP\x0c\xfceR\x03\x84\x91=\x02\x00\x00\\\n\x93\x00' +
          b'\x08\x14\x00>\n\xaaP\x0b\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00' +
          b'\x93\x00\t\x15\x00\xb7\n\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00' +
          b'\xad\x04\x92\x00\t\x16\x000\x0b\xaaP\x0b\xfceR\x03\x84\x91=\x02' +
          b'\x00\x00\x00\x00\x93\x00\t\x17\x00\xa9\x0b\xaaP\r\xfceR\x03\x84' +
          b'\x91=\x02\x00\x00\xd6\x03\x93\x00\x08\x18\x00"\x0c\xaaP\x0c\xfc' +
          b'eR\x03\x84\x91=\x02\x00\x00\x00\x00\x94\x00\x08\x19\x00\x9b\x0c' +
          b'\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x94\x00\n\x1a\x00' +
          b'\x14\r\xaaP\t\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x94\x00\x0b' +
          b'\x1b\x00\x8d\r\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x95' +
          b'\x00\x0c\x1c\x00\x06\x0e\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00' +
          b'\x00\x00\x95\x00\n\x1d\x00\x7f\x0e\xaaP\n\xfceR\x03\x84\x91=\x02' +
          b'\x00\x00k\x03\x95\x00\x0b\x1e\x00\xf8\x0e\xaaP\n\xfceR\x03\x84' +
          b'\x91=\x02\x00\x00\x00\x00\x97\x00\n\x1f\x00q\x0f\xaaP\t\xfceR' +
          b'\x03\x84\x91=\x02\x00\x00\x00\x00\x97\x00\r \x00\xea\x0f\xaaP' +
          b'\x0c\xfceR\x03\x84\x91=\x02\x00\x00~\x04\x96\x00\n!\x00c\x10' +
          b'\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x96\x00\x0b"\x00' +
          b'\xdc\x10\xaaP\x08\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x96' +
          b'\x00\x0e#\x00U\x11\xaaP\x08\xfceR\x03\x84\x91=\x02\x00\x00V\t' +
          b'\x96\x00\x0c$\x00\xce\x11\xaaP\n\xfceR\x03\x84\x91=\x02\x00\x00' +
          b'\x00\x00\x97\x00\n%\x00G\x12\xaaP\x0c\xfceR\x03\x84\x91=\x02' +
          b'\x00\x00\xec\t\x97\x00\n&\x00\xc0\x12\xaaP\x0c\xfceR\x03\x84' +
          b'\x91=\x02\x00\x00\x00\x00\x97\x00\n\'\x009\x13\xaaP\n\xfceR\x03' +
          b'\x84\x91=\x02\x00\x00\x00\x00\x97\x00\n(\x00\xb2\x13\xaaP\n\xfc' +
          b'eR\x03\x84\x91=\x02\x00\x00\x00\x00\x97\x00\x0c)\x00+\x14\xaaP' +
          b'\x0b\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x98\x00\t*\x00\xa4' +
          b'\x14\xaaP\x08\xfceR\x03\x84\x91=\x02\x00\x00\x00\x00\x99\x00' +
          b'\x12+\x00\x1d\x15\xaaP\x0c\xfceR\x03\x84\x91=\x02\x00\x00\xad' +
          b'\x06\x9b\x00\t,\x00\x96\x15\xaaP\x0b\xfceR\x03\x84\x91=\x02\x00' +
          b'\x00\x00\x00\x9b\x00\n\x98+')
        self.assertEqual(len(packets), 1)
        packet = packets[0]
        self.assertEqual(isinstance(packet, PacketData), True)
        self.assertEqual(len(packet.items), 45)
        packetItem = packet.items[3]
        self.assertEqual(isinstance(packetItem, PacketDataItem), True)
        self.assertEqual(packetItem.params['speed'], 0.3)
        self.assertEqual(packetItem.params['latitude'], 55.731708)
        self.assertEqual(packetItem.params['longitude'], 37.589364)
        self.assertEqual(packetItem.params['satellitescount'], 7)
        self.assertEqual(packetItem.params['time'].
            strftime('%Y-%m-%dT%H:%M:%S.%f'), '2012-11-19T09:58:06.000000')
        packetItem2 = packet.items[6]
        self.assertEqual(packetItem2.params['speed'], 0)
        self.assertEqual(packetItem2.params['satellitescount'], 9)
        self.assertEqual(packetItem2.number, 6)
        self.assertEqual(packetItem2.additional, b'')
