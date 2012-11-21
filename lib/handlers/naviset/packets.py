# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset packets
@copyright 2012, Maprox LLC
'''

import time
from datetime import datetime
from struct import unpack, pack, calcsize
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
        self.__command = Command.CMD_GET_STATUS;

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

class PacketData(Packet):
    """
      Data packet of naviset messaging protocol
    """

    def _parseBody(self, body):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(Packet, self)._parseBody(body)

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        return super(Packet, self)._buildBody()

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

  def test_commandPacket(self):
    """
    packet = Packet()
    packet.header = 1
    tagslist = []
    tagslist.append(tags.Tag.getInstance(3, b'2345545456444445'))
    tagslist.append(tags.Tag.getInstance(4, b'\x03\x04'))
    tagslist.append(tags.Tag.getInstance(0xE0, b'\xFA\x72\x50\x25'))
    tagslist.append(tags.Tag.getInstance(0xE1, b'Makephoto 1'))
    packet.tags = tagslist
    self.assertEqual(packet.rawData, b'\x01&\x00\x032345545456444445\x04\x03\x04\xe0\xfarP%\xe1\x0bMakephoto 1\xbc\xb5')

  def test_answerPacketPhoto(self):
    packet = Packet(b'\x01"\x00\x03868204000728070\x042\x00\xe0\x01\x00\x00\x00\xe1\x08Photo ok\x13\xf6')
    self.assertEqual(packet.header, 1)
    self.assertEqual(packet.length, 34)
    self.assertEqual(packet.hasTag(0x03), True)
    self.assertEqual(packet.hasTag(0xe2), False)
    self.assertEqual(packet.getTag(0xe1).getValue(), 'Photo ok')
  """