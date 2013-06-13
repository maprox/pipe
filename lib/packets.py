# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Abstract binary packets
@copyright 2013, Maprox LLC
'''

from struct import *

# ---------------------------------------------------------------------------

class SolidBinaryPacket(object):
    """
     Solid binary packet, which can not determine its length
    """
    # protected properties
    _head = None
    _body = None
    _tail = None
    _rawData = None
    _rebuild = True       # flag to rebuild rawData

    def __init__(self, data = None, config = None):
        """
         Constructor
         @param data: Input binary data
         @param params: Input parameters
        """
        self.configure(config)
        self.rawData = data

    def configure(self, config):
        """
         Configuration
         @param config: dict
         @return:
        """
        pass

    @property
    def rawData(self):
        if self._rebuild: self._build()
        return self._rawData

    @rawData.setter
    def rawData(self, value):
        self._rebuild = False
        self._rawData = value
        self._parse()

    @property
    def head(self):
        if self._rebuild: self._build()
        return self._head

    @property
    def body(self):
        if self._rebuild: self._build()
        return self._body

    @body.setter
    def body(self, value):
        self._body = value
        self._parseBody()
        self._rebuild = True

    @property
    def tail(self):
        if self._rebuild: self._build()
        return self._tail

    def _parse(self):
        """
         Parses rawData
        """
        if self._rawData == None: return
        self._offset = 0
        self._parseHead()
        self._parseBody()
        self._parseTail()

    def _parseHead(self):
        """
         Parses packet's head
         @return: self
        """
        return self

    def _parseBody(self):
        """
         Parses body of the packet
         @return: self
        """
        return self

    def _parseTail(self):
        """
         Parses tail of the packet
         @return: self
        """
        return self

    def _build(self):
        """
         Builds rawData from object variables
         @return: self
        """
        self._rebuild = False
        self._head = self._buildHead()
        self._body = self._buildBody()
        self._tail = self._buildTail()
        self._rawData = self._buildRawData()
        return self

    def _buildHead(self):
        """
         Builds head of the packet
         @return: head binstring
        """
        return self._head

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        return self._body

    def _buildTail(self):
        """
         Builds tail of the packet
         @return: tail binstring
        """
        return self._tail

    def _buildRawData(self):
        """
         Builds raw data of the packet
         @return: rawData binstring
        """
        head = self._head if self._head is not None else b''
        body = self._body if self._body is not None else b''
        tail = self._tail if self._tail is not None else b''
        return head + body + tail

    def readFrom(self, fmt, buffer = None):
        """
         Reads data from buffer, and increases offset
         @param fmt: pack() format string
         @param buffer: buffer from which we will get the result
         @param offset: offset wich will be increased
         @return: int
        """
        if fmt is None:
            return None
        if buffer is None:
            buffer = self._rawData
        fmtSize = calcsize(fmt)
        shift = self._offset + fmtSize
        result = unpack(fmt, buffer[self._offset:shift])[0]
        self._offset += fmtSize
        return result

# ---------------------------------------------------------------------------

class BinaryPacket(SolidBinaryPacket):
    """
     Abstract binary protocol packet which can determine its length
     and through this cut the tail of supplied raw data
    """

    # protected properties
    _rawDataTail = None

    @property
    def rawDataTail(self):
        return self._rawDataTail

    def _parseTail(self):
        """
         Parses packet's tail.
         By default it cuts the unused tail of packet buffer.
         @return: self
        """
        # cut the tail
        self._rawDataTail = self._rawData[self._offset:]
        self._rawData = self._rawData[:self._offset]
        return self

# ---------------------------------------------------------------------------

class BasePacket(BinaryPacket):
    """
     Abstract binary protocol packet with length and checksum
    """

    # protected properties
    _header = None
    _length = 0
    _checksum = None
    _offset = 0

    _fmtHeader = None   # header format
    _fmtLength = None   # packet length format
    _fmtChecksum = None # checksum format

    @property
    def header(self):
        if self._rebuild: self._build()
        return self._header

    @header.setter
    def header(self, value):
        self._header = value
        self._rebuild = True

    @property
    def length(self):
        if self._rebuild: self._build()
        return self._length

    @property
    def checksum(self):
        if self._rebuild: self._build()
        return self._checksum

    def _parseHeader(self):
        """
         Parses header data.
         If return None, then offset is shifted to calcsize(self._fmtHeader)
         otherwise to the returned value
         @return:
        """
        return None

    def _parseLength(self):
        """
         Parses packet length data.
         If return None, then offset is shifted to calcsize(self._fmtLength)
         otherwise to the returned value
         @return:
        """
        return None

    def _parseChecksum(self):
        """
         Parses checksum data.
         If return None, then offset is shifted to calcsize(self._fmtChecksum)
         otherwise to the returned value
         @return:
        """
        return None

    def calculateChecksum(self):
        """
         Returns calculated checksum
         @return: int
        """
        return 0

    def _isCorrectChecksum(self):
        """
         Returns true if given checksum equals to the calculated
         @return: True if given checksum equals to the calculated
         """
        return self.calculateChecksum() == self.checksum

    def _parseHead(self):
        """
         Parses packet header
         @return: self
        """
        #print (self._rawData)
        super(BasePacket, self)._parseHead()
        buffer = self._rawData
        self._head = b''

        # read header and length
        fmt = self._fmtHeader
        fmtSize = calcsize(fmt or '')
        shift = self._offset + fmtSize
        if fmt is not None:
            self._header = unpack(fmt, buffer[self._offset:shift])[0]
            self._head = buffer[:shift]
        self._offset += self._parseHeader() or fmtSize

        fmt = self._fmtLength
        fmtSize = calcsize(fmt or '')
        shift = self._offset + fmtSize
        if fmt is not None:
            self._length = unpack(fmt, buffer[self._offset:shift])[0]
            self._head = buffer[:shift]
        self._offset += self._parseLength() or fmtSize

        self._body = b''
        if self._length > 0:
            self._body = buffer[self._offset:self._offset + self._length]
            if len(self._body) != self._length:
                raise Exception('Body length is incorrect! ' +\
                    str(self._length) + ' (given) != ' + \
                    str(len(self._body)) + ' (must be)')
        self._offset += self._length
        return self

    def _parseTail(self):
        """
         Parses packet tail
         @return: self
        """
        buffer = self._rawData
        self._tail = b''

        # read checksum and compare with calculated checksum
        fmt = self._fmtChecksum
        fmtSize = calcsize(fmt or '')
        shift = self._offset + fmtSize
        if fmt is not None:
            self._checksum = unpack(fmt, buffer[self._offset:shift])[0]
            self._tail = buffer[self._offset:shift]
            # checksum check
            if not self._isCorrectChecksum():
                raise Exception('Checksum is incorrect! ' +
                    str(self.checksum) + ' (given) != ' + \
                    str(self.calculateChecksum()) + ' (must be)')
        self._offset += self._parseChecksum() or fmtSize

        return super(BasePacket, self)._parseTail()

    def _buildHead(self):
        """
         Builds buffer's head
         @protected
        """
        data = b''
        if self._fmtHeader is not None:
            if self._header is None:
                self._header = 0
            data += pack(str(self._fmtHeader), self._header)
        if self._fmtLength is not None:
            data += pack(str(self._fmtLength), self._buildCalculateLength())
        return data

    def _buildTail(self):
        """
         Builds buffer's tail
         @protected
        """
        data = b''
        if self._fmtChecksum is not None:
            self._checksum = self.calculateChecksum()
            data = pack(str(self._fmtChecksum), self._checksum)
        return data

    def _buildCalculateLength(self):
        """
         Calculates length of the packet
         @return: int
        """
        self._length = 0
        if self._body is not None:
            self._length = len(self._body)
        return self._length