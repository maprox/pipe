# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack packets
@copyright 2013, Maprox LLC
'''

from datetime import datetime
from struct import *
import lib.crc16 as crc16
from lib.packets import *

# ---------------------------------------------------------------------------

class PacketKeepAlive(BasePacket):
    """
      Keep alive packet of ATrack messaging protocol
    """

    # public properties
    headerPrefix = b'\xFE\x02'

    # protected properties
    _fmtHeader = '>H'   # header format
    _fmtLength = None   # packet length format
    _fmtChecksum = None # checksum format

    __unitId = None
    __sequenceId = 0

    def __init__(self, data = None):
        """
         Initialize command with specific params
         @param params: dict
         @return:
        """
        if isinstance(data, dict):
            self.setParams(data)
        else:
            super(PacketKeepAlive, self).__init__(data)
        self._rebuild = True

    def setParams(self, params):
        """
         Set command params if needed.
         Override in child classes.
         @param params: dict
         @return:
        """
        self.__unitId = params['unitId'] or ''
        self.__sequenceId = params['sequenceId'] or 0

    @property
    def unitId(self):
        if self._rebuild: self._build()
        return self.__unitId

    @unitId.setter
    def unitId(self, value):
        if len(value) <= 15:
            self.__unitId = value
            self._rebuild = True

    @property
    def sequenceId(self):
        if self._rebuild: self._build()
        return self.__sequenceId

    @sequenceId.setter
    def sequenceId(self, value):
        if (0 <= value <= 0xFFFF):
            self.__sequenceId = value
            self._rebuild = True

    def _parseLength(self):
        """
         Parses length of the packet
         @param body: Body bytes
         @protected
        """
        # read header and length
        self._length = 10

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketKeepAlive, self)._parseBody()
        unitId, seqId = unpack('>QH', self._body)
        self.__unitId = str(unitId)
        self.__sequenceId = seqId
        return self

    def _buildHead(self):
        """
         Builds head of the packet
         @return: head binstring
        """
        self._head = self.headerPrefix
        return self._head

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        #result = super(PacketKeepAlive, self)._buildBody()
        result = b''
        result += pack('>Q', int(self.__unitId or '0'))
        result += pack('>H', self.__sequenceId)
        return result

# ---------------------------------------------------------------------------

class PacketCommandResponse(BasePacket):
    """
      Command answer packet of ATrack messaging protocol
    """

    # public properties
    headerPrefix = b'$'

    # protected properties
    _fmtHeader = '>B'   # header format
    _fmtLength = None   # packet length format
    _fmtChecksum = None # checksum format
    _params = None

    __command = None
    __tag = None
    __params = None

    @property
    def command(self):
        if self._rebuild: self._build()
        return self.__command

    @command.setter
    def command(self, value):
        self.__command = value
        self._rebuild = True

    @property
    def tag(self):
        if self._rebuild: self._build()
        return self.__tag

    @tag.setter
    def tag(self, value):
        self.__tag = value
        self._rebuild = True

    @property
    def params(self):
        if self._rebuild: self._build()
        return self._params

    def _parseLength(self):
        """
         Parses length of the packet
         @param body: Body bytes
         @protected
        """
        # read header and length
        self._length = 10

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketCommandResponse, self)._parseBody()
        unitId, seqId = unpack('>QH', self._body)
        self.__unitId = str(unitId)
        self.__sequenceId = seqId
        return self

    def _buildHead(self):
        """
         Builds head of the packet
         @return: head binstring
        """
        self._head = self.headerPrefix
        return self._head

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        #result = super(PacketKeepAlive, self)._buildBody()
        result = b''
        result += pack('>Q', int(self.__unitId or '0'))
        result += pack('>H', self.__sequenceId)
        return result

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
            if len(data) == 0: break
        return packets

    @classmethod
    def getInstance(cls, data = None):
        """
          Returns a packet instance by its number
          @return: BasePacket instance
        """
        if data == None: return
        CLASS = PacketKeepAlive
        # read prefix
        pka_HeaderPrefix = PacketKeepAlive.headerPrefix
        pcr_HeaderPrefix = PacketCommandResponse.headerPrefix
        if data[:len(pka_HeaderPrefix)] == pka_HeaderPrefix:
            CLASS = PacketKeepAlive
        elif data[:len(pcr_HeaderPrefix)] == pcr_HeaderPrefix:
            CLASS = PacketCommandResponse
        if not CLASS:
            raise Exception('Unknown packet structure')
        return CLASS(data)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_keepAlivePacket(self):
        buffer = b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x01'
        packets = PacketFactory.getPacketsFromBuffer(buffer)
        p = packets[0]
        self.assertIsInstance(p, PacketKeepAlive)
        self.assertEqual(p.sequenceId, 1)
        self.assertEqual(p.unitId, '352964050784040')

        pka2 = PacketKeepAlive({
            'unitId': '352964050784040',
            'sequenceId': 15
        })
        self.assertEqual(pka2.rawData,
            b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x0f')

        pka = PacketKeepAlive()
        pka.unitId = '352964050784040'
        pka.sequenceId = 22
        self.assertEqual(pka.rawData,
            b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x16')

    def test_commandResponse(self):
        buffer = b'$OK\r\n'
        #packets = PacketFactory.getPacketsFromBuffer(buffer)
        #p = packets[0]
        #self.assertIsInstance(p, PacketCommandResponse)

    def test_packetData(self):
        #packets = PacketFactory.getPacketsFromBuffer(
        #    b'@P\xec\xc0\x00U\x00\x1a\x00\x01A\x04\xd8\xdd\x8f)Q\x90\xc2' +
        #    b'\xedQ\x90\xc2\xedQ\x94\xdc\xbc\x02>\xa5\xc0\x03SDt\x00\x00' +
        #    b'\x02\x00\x00\t\xcd\x00\x15\x00\x00\x00\x00\x00\x00\x00\x00' +
        #    b'\x00\x00\x00\x00\x07\x00\x82\x00\x00\x00\x00\x00\x00\x00' +
        #    b'\x00\x00\x00\x00\x00\x00\x9e\x00\x00\x02\x00\x00\x00\x00' +
        #    b'\x00\x00\xff\xd8\x00\x00\x00\x00\x00\x00'
        #)
        pass