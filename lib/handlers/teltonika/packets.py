# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika packets
@copyright 2012, Maprox LLC
'''

import time
from datetime import datetime, timedelta
from struct import *
import lib.bits as bits
import lib.crc16 as crc16
from lib.packets import *

# ---------------------------------------------------------------------------

class PacketHead(BasePacket):
    """
      Head packet of teltonika messaging protocol
    """
    # protected properties
    _fmtHeader = None   # header format
    _fmtLength = '>H'   # packet length format
    _fmtChecksum = None # checksum format
    _deviceImei = 0

    @property
    def deviceImei(self):
        if self._rebuild: self._build()
        return self._deviceImei

    @deviceImei.setter
    def deviceImei(self, value):
        if (len(value) > 0):
            self._deviceImei = str(value)
            self._rebuild = True

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        self._deviceImei = self.body.decode()
        return self

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketHead, self)._buildBody()
        result += self._deviceImei.encode()
        return result

# ---------------------------------------------------------------------------

class PacketData(BasePacket):
    """
      Data packet of teltonika messaging protocol.
    """
    _fmtHeader = '>l'   # header format
    _fmtLength = '>l'   # packet length format
    _fmtChecksum = '>H' # checksum format
    _AvlDataArray = None

    @property
    def AvlDataArray(self):
        if self._rebuild: self._build()
        return self._AvlDataArray

    def __init__(self, data = None):
        """
         Constructor
         @param data: Binary data of data packet
         @return: PacketData instance
        """
        super(PacketData, self).__init__(data)

    def _parseHeader(self):
        """
         Parses rawData
        """
        zeroes = 0x00000000
        if (self._header != zeroes):
            raise Exception('Incorrect data packet! ' +\
                str(self._header) + ' (given) != ' + \
                str(zeroes) + ' (must be)')

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketData, self)._parseBody()
        self._AvlDataArray = AvlDataArray(self._body)

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketData, self)._buildBody()
        result += AvlDataArray.rawData
        return result

    def getChecksum(self, buffer):
        """
         Calculates CRC (CRC-16 Modbus)
         @param buffer: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        data = self._head + self._body
        return crc16.Crc16.calcBinaryString(data, crc16.INITIAL_MODBUS)

# ---------------------------------------------------------------------------

class AvlDataArray(SolidBinaryPacket):
    """
      Item of data packet of naviset messaging protocol
    """
    # private properties
    _itemsCount = 0
    _items = None
    _codecId = 0

    @property
    def items(self):
        return self._items

    @property
    def codecId(self):
        if self._rebuild: self._build()
        return self._codecId

    @codecId.setter
    def codecId(self, value):
        self._codecId = value
        self._rebuild = True

    def _parseHead(self):
        """
         Parses packet's head
         @return: self
        """
        buffer = self._rawData
        # get codecId
        fmt = '>B'
        fmtLength = calcsize(fmt)
        self._codecId = unpack(fmt,
            buffer[self._offset:self._offset + fmtLength])[0]
        self._offset += 1
        # get count of items
        self._itemsCount = unpack(fmt,
            buffer[self._offset:self._offset + fmtLength])[0]
        self._offset += 1
        # body
        self._body = self._rawData[self._offset:-1]
        # retrieving Avl data items
        self._items = AvlData.getAvlDataListFromBuffer(self._body)
        self._tail = self._rawData[-1:]
        # last byte must be equal to self._itemsCount
        lastByte = unpack(fmt, self._tail)[0]
        if lastByte != self._itemsCount:
            raise Exception('Incorrect count of items in AVL data array! ' +\
                str(self._itemsCount) + ' (head) != ' +\
                str(lastByte) + ' (tail)')
        return self

# ---------------------------------------------------------------------------

class AvlData(BinaryPacket):
    """
      Item of data packet of naviset messaging protocol
    """
    # protected properties
    _timestamp = None
    _priority = None
    _longitude = None
    _latitude = None
    _altitude =  None
    _angle = None
    _satellitesCount = None
    _speed = None
    _ioElement = None

    @property
    def timestamp(self):
        if self._rebuild: self._build()
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value
        self._rebuild = True

    @property
    def datetime(self):
        if self._rebuild: self._build()
        return datetime.utcfromtimestamp(self._timestamp / 1000)

    @datetime.setter
    def datetime(self, value):
        self._timestamp = int(value.strftime("%s"))
        self._rebuild = True

    @property
    def priority(self):
        if self._rebuild: self._build()
        return self._priority

    @priority.setter
    def priority(self, value):
        self._priority = value
        self._rebuild = True

    @property
    def longitude(self):
        if self._rebuild: self._build()
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._longitude = value
        self._rebuild = True

    @property
    def latitude(self):
        if self._rebuild: self._build()
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._latitude = value
        self._rebuild = True

    @property
    def altitude(self):
        if self._rebuild: self._build()
        return self._altitude

    @altitude.setter
    def altitude(self, value):
        self._altitude = value
        self._rebuild = True

    @property
    def angle(self):
        if self._rebuild: self._build()
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self._rebuild = True

    @property
    def satellitesCount(self):
        if self._rebuild: self._build()
        return self._satellitesCount

    @satellitesCount.setter
    def satellitesCount(self, value):
        self._satellitesCount = value
        self._rebuild = True

    @property
    def speed(self):
        if self._rebuild: self._build()
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value
        self._rebuild = True

    @property
    def ioElement(self):
        if self._rebuild: self._build()
        return self._ioElement

    @ioElement.setter
    def ioElement(self, value):
        self._ioElement = value
        self._rebuild = True

    def _parseBody(self):
        """
         Parses packet's head
         @return: self
        """
        super(AvlData, self)._parseBody()
        self._body = self._rawData
        self._timestamp = self.readFrom('>Q')
        self._priority = self.readFrom('>B')
        precision = 10000000
        self._longitude = self.readFrom('>l') / precision
        self._latitude = self.readFrom('>l') / precision
        self._altitude = self.readFrom('>H')
        self._angle = self.readFrom('>H')
        self._satellitesCount = self.readFrom('>B')
        self._speed = self.readFrom('>H')

        # get ioElement
        eventIoId = self.readFrom('>B')
        items = []
        ioTotalCount = self.readFrom('>B')
        ioOneByteCount = self.readFrom('>B')
        cnt = 0
        while cnt < ioOneByteCount:
            items.append({
                'id': self.readFrom('>B'),
                'value': self.readFrom('>B')
            })
            cnt += 1
        ioTwoByteCount = self.readFrom('>B')
        cnt = 0
        while cnt < ioTwoByteCount:
            items.append({
                'id': self.readFrom('>B'),
                'value': self.readFrom('>H')
            })
            cnt += 1
        ioFourByteCount = self.readFrom('>B')
        cnt = 0
        while cnt < ioFourByteCount:
            items.append({
                'id': self.readFrom('>B'),
                'value': self.readFrom('>L')
            })
            cnt += 1
        ioEightByteCount = self.readFrom('>B')
        cnt = 0
        while cnt < ioEightByteCount:
            items.append({
                'id': self.readFrom('>B'),
                'value': self.readFrom('>Q')
            })
            cnt += 1

        self._ioElement = {
            # Event IO ID – if data is acquired on event – this field
            # defines which IO property has changed and generated an event.
            # If data cause is not event – the value is 0.
            'eventIoId': eventIoId,
            # List of IO elements
            'items': items
        }
        return self

    @classmethod
    def getAvlDataListFromBuffer(cls, data = None):
        """
         Returns an array of AvlData instances from data
         @param data: Input binary data
         @return: array of AvlData instances (empty array if no AvlData found)
        """
        items = []
        while True:
            item = AvlData(data)
            data = item.rawDataTail
            items.append(item)
            if (len(data) == 0): break
        return items

# ---------------------------------------------------------------------------

class TeltonikaConfiguration(BasePacket):
    """
      Item of data packet of naviset messaging protocol
    """
    _fmtLength = '>H'   # packet length format
    _packetId = 0
    _items = None

    def _parseLength(self):
        """
         Parses packet length data.
         If return None, then offset is shifted to calcsize(self._fmtLength)
         otherwise to the returned value
         @return:
        """


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
    def getInstance(cls, data = None):
        """
          Returns a tag instance by its number
          @return: BasePacket instance
        """
        if data == None: return
        CLASS = PacketHead
        # read header and length
        length = unpack(">H", data[:2])[0]
        if length == 0:
            CLASS = PacketData
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
        packet = PacketFactory.getInstance(b'\x00\x0f012896001609129')
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(isinstance(packet, PacketData), False)
        self.assertEqual(packet.length, 15)
        self.assertEqual(packet.body, b'012896001609129')
        self.assertEqual(packet.deviceImei, '012896001609129')

    def test_AvlDataArray(self):
        data = b'\x08\x04\x00\x00\x01\x13\xfc\x20\x8d\xff\x00\x0f\x14\xf6' + \
            b'\x50\x20\x9c\xca\x80\x00\x6f\x00\xd6\x04\x00\x04\x00\x04\x03' + \
            b'\x01\x01\x15\x03\x16\x03\x00\x01\x46\x00\x00\x01\x5d\x00\x00' + \
            b'\x00\x01\x13\xfc\x17\x61\x0b\x00\x0f\x14\xff\xe0\x20\x9c\xc5' + \
            b'\x80\x00\x6e\x00\xc0\x05\x00\x01\x00\x04\x03\x01\x01\x15\x03' + \
            b'\x16\x01\x00\x01\x46\x00\x00\x01\x5e\x00\x00\x00\x01\x13\xfc' + \
            b'\x28\x49\x45\x00\x0f\x15\x0f\x00\x20\x9c\xd2\x00\x00\x95\x01' + \
            b'\x08\x04\x00\x00\x00\x04\x03\x01\x01\x15\x00\x16\x03\x00\x01' + \
            b'\x46\x00\x00\x01\x5d\x00\x00\x00\x01\x13\xfc\x26\x7c\x5b\x00' + \
            b'\x0f\x15\x0a\x50\x20\x9c\xcc\xc0\x00\x93\x00\x68\x04\x00\x00' + \
            b'\x00\x04\x03\x01\x01\x15\x00\x16\x03\x00\x01\x46\x00\x00\x01' + \
            b'\x5b\x00\x04'
        avl = AvlDataArray(data)
        self.assertEqual(avl.codecId, 8)
        self.assertEqual(len(avl.items), 4)
        item = avl.items[0]
        self.assertEqual(item.datetime.
            strftime('%Y-%m-%dT%H:%M:%S.%f'), '2007-07-25T06:46:38.335000')
        self.assertEqual(item.priority, 0)
        self.assertEqual(item.longitude, 25.3032016)
        self.assertEqual(item.latitude, 54.7146368)
        self.assertEqual(item.altitude, 111)
        self.assertEqual(item.angle, 214)
        self.assertEqual(item.satellitesCount, 4)
        self.assertEqual(item.speed, 4)
        self.assertEqual(item.ioElement, {
            'eventIoId': 0,
            'items': [{'id': 1,  'value': 1},
                      {'id': 21, 'value': 3},
                      {'id': 22, 'value': 3},
                      {'id': 70, 'value': 349}]
        })

    def test_PacketData(self):
        data = b'\x00\x00\x00\x00\x00\x00\x00\x2c\x08\x01\x00\x00\x01\x13' + \
               b'\xfc\x20\x8d\xff\x00\x0f\x14\xf6\x50\x20\x9c\xca\x80\x00' + \
               b'\x6f\x00\xd6\x04\x00\x04\x00\x04\x03\x01\x01\x15\x03\x16' + \
               b'\x03\x00\x01\x46\x00\x00\x01\x5d\x00\x01\x00\x00'
        packet = PacketData(data)
        avl = packet.AvlDataArray
        self.assertEqual(avl.codecId, 8)
        self.assertEqual(len(avl.items), 1)

    def test_readConfigurationPacket(self):
        data = b'\x00\x92\x8c\x00\x1b\x03\xe8\x00\x01\x30\x03\xf2\x00\x01' + \
               b'\x31\x03\xf3\x00\x02\x32\x30\x03\xf4\x00\x02\x31\x30\x03' + \
               b'\xfc\x00\x01\x30\x04\x06\x00\x01\x30\x04\x07\x00\x01\x30' + \
               b'\x04\x08\x00\x01\x30\x04\x09\x00\x01\x30\x04\x0a\x00\x01' + \
               b'\x30\x04\x10\x00\x01\x30\x04\x11\x00\x01\x30\x04\x12\x00' + \
               b'\x01\x30\x04\x13\x00\x01\x30\x04\x14\x00\x01\x30\x04\x1a' +\
               b'\x00\x01\x30\x04\x1b\x00\x01\x30\x04\x1c\x00\x01\x30\x04' +\
               b'\x1d\x00\x01\x30\x04\x1e\x00\x01\x30\x04\x24\x00\x01\x30' +\
               b'\x04\x25\x00\x01\x30\x04\x26\x00\x01\x30\x04\x27\x00\x01' +\
               b'\x30\x04\x28\x00\x01\x30\x0c\xbd\x00\x0c\x2b\x33\x37\x30' +\
               b'\x34\x34\x34\x34\x34\x34\x34\x34'
        packet = TeltonikaConfiguration(data)
        self.assertEqual(packet.length, 146)