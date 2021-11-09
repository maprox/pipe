# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Galileo tags
@copyright 2012, Maprox LLC
'''

from struct import unpack, pack
import lib.bits as bits
import lib.crc16 as crc16
import lib.handlers.galileo.tags as tags

from kernel.utils import NeedMoreDataException
from lib.factory import AbstractPacketFactory

# ---------------------------------------------------------------------------

class BasePacket(object):
    """
     Default galileo protocol packet
    """

    # private properties
    __header = 0
    __length = 0
    __rawData = None
    __rawDataTail = None
    __body = None
    __crc = 0
    __convert = True
    __archive = False

    @classmethod
    def getPacketsFromBuffer(cls, data = None):
        """
         Returns an array of BasePacket instances from data
         @param data: Input binary data
         @return array of BasePacket instances (empty array if no packet)
        """
        packets = []
        while True:
            packet = cls(data)
            data = packet.rawDataTail
            packets.append(packet)
            if len(data) == 0: break
        return packets

    def __init__(self, data = None):
        """
         Constructor
         @param data: Input binary data
        """
        self.rawData = data

    def isHalved(self, header):
        """
         Returns True if length of the packet is in 15 bits
         Returns False if length of the packet is in 16 bits
         @param header: int number of packet header
        """
        return False

    def rebuild(self):
        """
         Mark packet to rebuilt later
        """
        self.__convert = True

    @property
    def header(self):
        if self.__convert: self.__build()
        return self.__header

    @header.setter
    def header(self, value):
        self.__header = value
        self.rebuild()

    @property
    def archive(self):
        if self.__convert: self.__build()
        return self.__archive

    @archive.setter
    def archive(self, value):
        self.__archive = value
        self.rebuild()

    @property
    def rawDataTail(self):
        return self.__rawDataTail

    @property
    def rawData(self):
        if self.__convert: self.__build()
        return self.__rawData

    @rawData.setter
    def rawData(self, value):
        self.__convert = False
        self.__rawData = value
        self.__parse()

    @property
    def length(self):
        return self.__length

    @property
    def crc(self):
        return self.__crc

    @property
    def body(self):
        if self.__convert: self.__build()
        return self.__body

    @body.setter
    def body(self, value):
        self.__body = value
        self._parseBody(value)
        self.rebuild()

    def __parse(self):
        """
         Parses rawData
        """
        buffer = self.__rawData
        if buffer == None: return

        # read header and length
        archive = False
        header, length = unpack("<BH", buffer[:3])
        if self.isHalved(header):
            archive = bits.bitTest(length, 15)
            length = bits.bitClear(length, 15)

        if length > len(buffer) + 5:
            raise NeedMoreDataException('Not enough data in buffer')

        crc = unpack("<H", buffer[length + 3:length + 5])[0]
        crc_data = buffer[:length + 3]
        if not self.isCorrectCrc(crc_data, crc):
            raise Exception('Crc Is incorrect!')

        # now let's read packet data
        # but before this, check tagsdata length
        body = buffer[3:length + 3]
        if len(body) != length:
            raise Exception('Body length Is incorrect!')

        # apply new data
        self.__rawDataTail = buffer[length + 5:]
        self.__rawData = buffer[:length + 5]
        self.__archive = archive
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
        self.__convert = False
        self.__header = self.__header
        self.__length = len(self.__body)
        length = self.__length
        if self.isHalved(self.__header):
            if self.__archive:
                length = bits.bitSet(self.__length, 15)

        self.__rawData = pack("<BH", self.__header, length)
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
    def isCorrectCrc(cls, buffer, crc):
        """
         Checks buffer CRC (CRC-16 Modbus)
         @param buffer: binary string
         @param crc: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        crc_calculated = crc16.Crc16.calcBinaryString(
          buffer, crc16.INITIAL_MODBUS)
        return crc == crc_calculated

    def __str__(self):
        return str(self.getValue())

# ---------------------------------------------------------------------------

class Packet(BasePacket):
    """
     Default galileo protocol packet
    """
    _tags = None
    _tagsMap = None

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value
        self.rebuild()

    @property
    def tagsMap(self):
        return self._tagsMap

    def isHalved(self, header):
        """
         Returns True if length of the packet is in 15 bits
         Returns False if length of the packet is in 16 bits
         @param header: int number of packet header
        """
        return (header == 1)

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        self._tags = None
        self._tagsMap = {}
        if (self.header == 1):
            tagsdata = body
            tagslist = []
            tail = 1
            length = len(body)
            while tail < length:
                tagnum = tagsdata[tail - 1]
                taglen = tags.getLengthOfTag(tagnum)
                if (taglen == 0):
                    taglen = length - tail
                elif (taglen < 0):
                    fmt = tags.Tag.getClass(tagnum).lengthfmt
                    taglen = unpack(fmt, tagsdata[tail : tail - taglen])[0]
                    tail += 1
                tagdata = tagsdata[tail : tail + taglen]
                tag = tags.Tag.getInstance(tagnum, tagdata)
                tagslist.append(tag)
                self._tagsMap[tagnum] = tag
                tail += taglen + 1

            self._tags = tagslist

        super(Packet, self)._parseBody(body)

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        if self.tags and (len(self.tags) > 0):
            result = b''
            for tag in self.tags:
                result += tag.getRawTag()
        else:
            return super(Packet, self)._buildBody()
        return result

    def hasTag(self, num):
        """
         Returns True if packet has tag with number 'num'
         @param num: Number of packet tag
        """
        return num in self._tagsMap

    def getTag(self, num):
        """
         Returns packet tag with number 'num'
         @param num: Number of packet tag
        """
        return self._tagsMap[num]

    def addTagInstance(self, tag):
        """
         Adds a tag to the packet
         @param tag: tags.Tag instance
        """
        if (self._tags == None): self._tags = []
        self._tags.append(tag)
        self.rebuild()
        return self

    def addTag(self, num, value):
        """
         Adds a tag to the packet
         @param num: Number of tag
         @param value: Value of tag
        """
        self.addTagInstance(tags.Tag.getInstance(num, value))
        return self

class PacketFactory(AbstractPacketFactory):
    
    def getInstance(self, data = None):
        if data == None: return
        return Packet(data)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_headPacket(self):
        packet = Packet(b'\x01\x17\x80\x01\n\x02w' +
          b'\x03868204000728070\x042\x00\x84\x90')
        self.assertEqual(packet.header, 1)
        self.assertEqual(packet.length, 23)
        self.assertEqual(packet.body,
          b'\x01\n\x02w\x03868204000728070\x042\x00')
        self.assertEqual(packet.crc, 36996)
        packet.header = 15
        packet.body = b'\x00\x00'
        self.assertEqual(packet.rawData, b'\x0F\x02\x00\x00\x00q\xb9')
        self.assertEqual(packet.length, 2)

    def test_newProtocolPacket(self):
        packet = Packet(b'\x01$\x80\x01\x0f\x02\xe6' +
          b'\x03868204008110347\x042\x00`\x00\x00a\x00\x00b\x00\x00\x8b\x00\x8c\x00?;')
        self.assertEqual(packet.header, 1)
        self.assertEqual(packet.length, 36)
        self.assertEqual(packet.body,
          b'\x01\x0f\x02\xe6\x03868204008110347\x042\x00`\x00\x00a\x00\x00b\x00\x00\x8b\x00\x8c\x00')
        self.assertEqual(packet.crc, 15167)

    def test_defaultPacket(self):
        packet = Packet(b'\x0F\x02\x00\x00\x00\x71\xB9')
        self.assertEqual(packet.header, 15)
        self.assertEqual(packet.length, 2)
        self.assertEqual(packet.body, b'\x00\x00')
        self.assertEqual(packet.crc, 47473)

    def test_commandPacket(self):
        packet = Packet()
        packet.header = 1
        tagslist = []
        tagslist.append(tags.Tag.getInstance(3, b'2345545456444445'))
        tagslist.append(tags.Tag.getInstance(4, b'\x03\x04'))
        tagslist.append(tags.Tag.getInstance(0xE0, b'\xFA\x72\x50\x25'))
        tagslist.append(tags.Tag.getInstance(0xE1, b'Makephoto 1'))
        packet.tags = tagslist
        self.assertEqual(packet.rawData, b'\x01&\x00\x032345545456444445' +
          b'\x04\x03\x04\xe0\xfarP%\xe1\x0bMakephoto 1\xbc\xb5')

    def test_answerPacketPhoto(self):
        packet = Packet(b'\x01"\x00\x03868204000728070\x042\x00\xe0' +
          b'\x01\x00\x00\x00\xe1\x08Photo ok\x13\xf6')
        self.assertEqual(packet.header, 1)
        self.assertEqual(packet.length, 34)
        self.assertEqual(packet.hasTag(0x03), True)
        self.assertEqual(packet.hasTag(0xe2), False)
        self.assertEqual(packet.getTag(0xe1).getValue(), 'Photo ok')

    def test_packetTail(self):
        packets = Packet.getPacketsFromBuffer(
          b'\x01\x17\x80\x01\n\x02w\x03868204000728070\x042\x00\x84\x90' +
          b'\x01"\x00\x03868204000728070\x042\x00\xe0\x01\x00\x00\x00' +
          b'\xe1\x08Photo ok\x13\xf6\x01"\x00\x03868204000728070\x042' +
          b'\x00\xe0\x01\x00\x00\x00\xe1\x08Photo ok\x13\xf6')
        self.assertEqual(len(packets), 3)