# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net>
@info      Galileo tags
@copyright 2012, Maprox LLC
'''

import time
from datetime import datetime
from struct import unpack, pack, calcsize
import lib.bits as bits
import lib.crc16 as crc16
import lib.handlers.galileo.tags as tags

# ---------------------------------------------------------------------------

class BasePacket(object):
  """
   Default galileo protocol packet
  """

  # private properties
  __header = 0
  __length = 0
  __rawdata = None
  __body = None
  __crc = 0
  __convert = True
  __archive = False
  __halvedPacket = True

  def __init__(self, data = None, halved = True):
    """
     Constructor
     @param data: Input binary data
     @param halved: True if length of the packet is in 15 bits
    """
    self.__halvedPacket = halved
    self.rawdata = data

  def isHalved(self, header):
    """
     Returns True if length of the packet is in 15 bits
     Returns False if length of the packet is in 16 bits
     @param header: int number of packet header
    """
    return self.__halvedPacket

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
  def rawdata(self):
    if self.__convert: self.__build()
    return self.__rawdata

  @rawdata.setter
  def rawdata(self, value):
    self.__convert = False
    self.__rawdata = value
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
     Parses rawdata
    """
    buffer = self.__rawdata
    if buffer == None: return
    crc = unpack("<H", buffer[-2:])[0]
    crc_data = buffer[:-2]
    if not self.isCorrectCrc(crc_data, crc):
       raise Exception('Crc Is incorrect!');

    # read header and length
    archive = False
    header, length = unpack("<BH", buffer[:3])
    if self.isHalved(header):
      archive = bits.bitTest(length, 15)
      length = bits.bitClear(length, 15)

    # now let's read packet data
    # but before this, check tagsdata length
    body = buffer[3:-2]
    if len(body) != length:
      raise Exception('Body length Is incorrect!');

    # apply new data
    self.__archive = archive
    self.__header = header
    self.__length = length
    self.__body = body
    self.__crc = crc
    # parse packet body
    self._parseBody(body)

  def __build(self):
    """
     Builds rawdata from object variables
     @protected
    """
    self.__body = self._buildBody()
    self.__convert = False
    self.__header = self.__header
    self.__length = len(self.__body)
    length = self.__length
    if self.__halvedPacket:
      if self.__archive:
        length = bits.bitSet(self.__length, 15)

    self.__rawdata = pack("<BH", self.__header, length)
    self.__rawdata += self.__body
    self.__crc = crc16.Crc16.calcBinaryString(
      self.__rawdata,
      crc16.INITIAL_MODBUS
    )
    self.__rawdata += pack("<H", self.__crc)

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

  _tags = None

  @property
  def tags(self):
    return self._tags

  @tags.setter
  def tags(self, value):
    self._tags = value
    self.rebuild()

  """
   Default galileo protocol packet
  """
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
          lengthfmt = tags.Tag.getClass(number).lengthfmt
          taglen = unpack(lengthfmt, tagdata[tail : tail - taglen])
          tail += 1
        tagdata = tagsdata[tail : tail + taglen]
        tagslist.append(tags.Tag.getInstance(tagnum, tagdata))
        tail += taglen + 1

      self._tags = tagslist

    super(Packet, self)._parseBody(body)

  def _buildBody(self):
    """
     Builds rawdata from object variables
     @protected
    """
    if self.tags and (len(self.tags) > 0):
      result = b''
      for tag in self.tags:
        result += tag.getRawTag()
    else:
      return super(Packet, self)._buildBody()
    return result

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

  def setUp(self):
    pass

  def test_headPacket(self):
    packet = Packet(b'\x01\x17\x80\x01\n\x02w\x03868204000728070\x042\x00\x84\x90')
    self.assertEqual(packet.header, 1)
    self.assertEqual(packet.length, 23)
    self.assertEqual(packet.body, b'\x01\n\x02w\x03868204000728070\x042\x00')
    self.assertEqual(packet.crc, 36996)
    packet.header = 15
    packet.body = b'\x00\x00'
    self.assertEqual(packet.rawdata, b'\x0F\x02\x80\x00\x00pQ')
    self.assertEqual(packet.length, 2)

  def test_defaultPacket(self):
    packet = Packet(b'\x0F\x02\x00\x00\x00\x71\xB9', False)
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
    self.assertEqual(packet.rawdata, b'\x01&\x00\x032345545456444445\x04\x03\x04\xe0\xfarP%\xe1\x0bMakephoto 1\xbc\xb5')
