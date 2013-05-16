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
import re


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

class PacketCommandResponse(BinaryPacket):
    """
      Command answer packet of ATrack messaging protocol
    """

    # public properties
    headerPrefix = b'$'

    # private properties
    __params = None
    __command = None
    __tag = None
    __params = None

    # patterns
    re_command = '\$(?P<command>\w+)\+?(?P<tag>\w+)?(=(?P<params>.+))?\r\n'
    re_params = '(("[^"]*")|[^,]+)*,?'

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
        return self.__params

    def _parseBody(self):
        """
         Parses body of the packet
         @return: self
        """
        data = self.rawData
        # let's work with text data
        data = data.decode()

        rc = re.compile(self.re_command, flags = re.IGNORECASE)
        rp = re.compile(self.re_params, flags = re.IGNORECASE)
        m = rc.search(data)
        if m:
            data_command = m.groupdict()
            self.__command = data_command['command']
            self.__tag = data_command['tag']
            self.__params = []
            self._offset += m.end()

            # let's parse the parameters
            params = data_command['params']
            if params:
                mp = rp.search(params)
                while mp.group(0):
                    self.__params.append(mp.group(1))
                    mp = rp.search(params, mp.end())

        return self

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
            if not data or len(data) == 0: break
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
        packets = PacketFactory.getPacketsFromBuffer(b'$OK\r\n')
        p = packets[0]
        self.assertIsInstance(p, PacketCommandResponse)
        self.assertEqual(p.command, 'OK')
        self.assertEqual(p.rawData, b'$OK\r\n')

    def test_multipleCommandResponse(self):
        packets = PacketFactory.getPacketsFromBuffer(
            b'$UNID=352964050784041\r\n$UNID=352964050784041\r\n' +
            b'$UNID=352964050784041\r\n$UNID=352964050784041\r\n' +
            b'$UNID=352964050784041\r\n$UNID=352964050784041\r\n' +
            b'$INFO+SOMETAG=352964050784041,AX5,Rev.1.08,352964050784041,' +
            b'250026811379271,897010268113792717,130,0,8,1,26,1,0\r\n' +
            b'$UNID=352964050784041\r\n$INFO=352964050784041,AX5,Rev.' +
            b'1.08,352964050784041,250026811379271,897010268113792717' +
            b',130,0,6,1,27,1,0\r\n$UNID=352964050784041\r\n' +
            b'$INFO=352964050784041,AX5,Rev.1.08,352964050784041,' +
            b'250026811379271,897010268113792717,130,0,7,1,27,1,0\r\n' +
            b'$UNID=352964050784041\r\n$INFO=352964050784041,AX5,Rev.' +
            b'1.08,352964050784041,250026811379271,897010268113792717' +
            b',129,0,9,1,27,1,0\r\n$UNID=352964050784041\r\n' +
            b'$INFO=352964050784041,AX5,Rev.1.08,352964050784041,' +
            b'250026811379271,897010268113792717,130,0,6,1,26,1,0\r\n' +
            b'$UNID=352964050784041\r\n$UNID=352964050784041\r\n'
        )
        self.assertEqual(len(packets), 17)
        p = packets[6]
        self.assertIsInstance(p, PacketCommandResponse)
        self.assertEqual(p.command, 'INFO')
        self.assertEqual(p.tag, 'SOMETAG')
        self.assertEqual(len(p.params), 13)
        self.assertEqual(p.params[2], 'Rev.1.08')
        self.assertEqual(p.params[10], '26')
        self.assertEqual(p.params[12], '0')

    def test_packetData(self):
        packets = PacketFactory.getPacketsFromBuffer(
            b'@P\xec\xc0\x00U\x00\x1a\x00\x01A\x04\xd8\xdd\x8f)Q\x90\xc2' +
            b'\xedQ\x90\xc2\xedQ\x94\xdc\xbc\x02>\xa5\xc0\x03SDt\x00\x00' +
            b'\x02\x00\x00\t\xcd\x00\x15\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x07\x00\x82\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x9e\x00\x00\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\xd8\x00\x00\x00\x00\x00\x00'
        )
        pass