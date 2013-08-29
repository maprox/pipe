# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Autolink packets
@copyright 2013, Maprox LLC
"""

from datetime import datetime
from struct import unpack, pack
import lib.bits as bits
import binascii
from lib.packets import *   
from lib.factory import AbstractPacketFactory

# ---------------------------------------------------------------------------

class AutolinkPacket(BasePacket):
    """
     Base packet for autolink protocol
    """
    _fmtHeader = '<H'   # header format

    # private properties
    __packetId = None

    def _parseHeader(self):
        """
         Parses header data.
         If return None, then offset is shifted to calcsize(self._fmtHeader)
         otherwise to the returned value
         @return:
        """
        self.__packetId = unpack("<B", self._head[:1])[0]
        return None

    @property
    def packetId(self):
        if self._rebuild: self._build()
        return self.__packetId

    @packetId.setter
    def packetId(self, value):
        if (0 <= value <= 0xFF):
            self.__packetId = value
            self._rebuild = True

# ---------------------------------------------------------------------------

class PacketHead(AutolinkPacket):
    """
      Head packet of autolink messaging protocol
    """
    # private properties
    __protocolVersion = None
    __deviceImei = None

    def _parseHeader(self):
        """
         Parses header data.
         If return None, then offset is shifted to calcsize(self._fmtHeader)
         otherwise to the returned value
         @return:
        """
        super(PacketHead, self)._parseHeader()
        self.__protocolVersion = unpack("<B", self._head[1:2])[0]
        return None

    def _parseLength(self):
        """
         Parses length of the packet
         @param body: Body bytes
         @protected
        """
        # read header and length
        self._length = 8

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketHead, self)._parseBody()
        self.__deviceImei = str(unpack('<Q', self._body)[0])

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketHead, self)._buildBody()
        result += pack('<Q', int(self.__deviceImei))
        return result

    @property
    def protocolVersion(self):
        if self._rebuild: self._build()
        return self.__protocolVersion

    @protocolVersion.setter
    def protocolVersion(self, value):
        if (0 <= value <= 0xFF):
            self.__protocolVersion = value
            self._rebuild = True

    @property
    def deviceImei(self):
        if self._rebuild: self._build()
        return self.__deviceImei

    @deviceImei.setter
    def deviceImei(self, value):
        self.__deviceImei = value
        self._rebuild = True

# ---------------------------------------------------------------------------

class PacketData(AutolinkPacket):
    """
      Data packet of autolink messaging protocol
    """

# ---------------------------------------------------------------------------
 

class PacketFactory(AbstractPacketFactory):
    """
     Packet factory
    """

    @classmethod
    def getClass(cls, packetPrefix):
        """
         Returns a tag class by number
         @param packetPrefix: one byte buffer
        """
        classes = {
            b'\xff': PacketHead,
            b'\x5b': PacketData
        }
        if not (packetPrefix in classes):
            return None
        return classes[packetPrefix]

    def getInstance(self, data = None):
        """
          Returns a tag instance by its number
        """
        if data == None: return

        # read packetId
        packetPrefix = data[:1]

        CLASS = self.getClass(packetPrefix)
        if not CLASS:
            raise Exception('Packet %s is not found' %
                binascii.hexlify(packetPrefix).decode())
        return CLASS(data)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.factory = PacketFactory()
        pass

    def test_headPacket(self):
        packet = self.factory.getInstance(
          b'\xff\x22\xf3\x0c\x45\xf5\xc9\x0f\x03\x00')
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(isinstance(packet, PacketData), False)
        self.assertEqual(packet.packetId, 255)
        self.assertEqual(packet.protocolVersion, 34)
        self.assertEqual(packet.deviceImei, '861785007918323')


    def test_packagePacket(self):
        packet = self.factory.getInstance(
            b'\x5B\x01\x01\x55\x00\xc5\xcf\xc2\x51' +
            b''
        )
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(isinstance(packet, PacketData), False)
        self.assertEqual(packet.packetId, 255)
        self.assertEqual(packet.protocolVersion, 34)
        self.assertEqual(pac