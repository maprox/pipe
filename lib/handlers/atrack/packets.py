# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack packets
@copyright 2013, Maprox LLC
'''

from datetime import datetime
from struct import *
import lib.bits as bits
import lib.crc16 as crc16
from lib.packets import *
from lib.factory import AbstractPacketFactory
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

class PacketCommand(BinaryPacket):
    """
      Command packet of ATrack messaging protocol
    """
    # private properties
    __command = None
    __tag = None
    __params = None

    def __init__(self, params = None):
        """
         Constructor
         @param data: Input binary data
         @param params: Input parameters
        """
        pass

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

    def _buildBody(self):
        """

         @return: bytes
        """
        buffer = b''
        buffer += self.__command.encode()
        if self.__tag:
            buffer += b'+' + self.__tag.encode()
        params = b''
        if self.__params:
            for param in self.__params:
                if len(params) > 0:
                    buffer += b','
                buffer += param.encode()
        buffer += b'\r\n'
        return buffer

# ---------------------------------------------------------------------------

class PacketCommandResponse(BinaryPacket):
    """
      Command answer packet of ATrack messaging protocol
    """

    # public properties
    headerPrefix = b'$'

    # private properties
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

    def _buildHead(self):
        """
         Returns head buffer
         @return: bytes
        """
        return self.headerPrefix

    def _buildBody(self):
        """

         @return: bytes
        """
        buffer = b''
        buffer += self.__command.encode()
        if self.__tag:
            buffer += b'+' + self.__tag.encode()
        params = b''
        if self.__params:
            for param in self.__params:
                if len(params) > 0:
                    buffer += b','
                buffer += param.encode()
        buffer += b'\r\n'
        return buffer

# ---------------------------------------------------------------------------

class PacketData(BasePacket):
    """
      Position report of ATrack messaging protocol
    """
    # public properties
    headerPrefix = b'@P'
    customInfo = ''
    timeFormat = 0

    # protected properties
    _fmtHeader = '>L'   # header format
    _fmtLength = '>H'    # length format

    # private properties
    __sequenceId = None
    __unitId = 0
    __items = None

    customInfoTable = {
        'SA': ('>B', 'sat_count'),
        'MV': ('>H', 'ext_battery_voltage'),
        'BV': ('>H', 'int_battery_voltage'),
        'GQ': ('>B', 'gsm_signal_quality'),
        'CE': ('>H', 'gsm_cell_id'),
        'LC': ('>H', 'gsm_cell_lac'),
        'CN': ('>L', 'gsm_mcc_mnc'),
        'RL': ('>B', 'gsm_rxlev'),
        'PC': ('>L', 'pulse_count_value'),
        'AT': ('>L', 'altitude'),
        'RP': ('>H', 'can_rpm'),
        'GS': ('>B', 'gsm_status'),
        'DT': ('>B', 'report_type'),
        'VN': (None, 'vin'),
        'MF': ('>H', 'can_mass_airflow_rate'),
        'EL': ('>B', 'can_engine_load'),
        'TR': ('>B', 'can_throttle_position'),
        'ET': ('>h', 'can_coolant_temperature'),
        'FL': ('>B', 'can_fuel_percent'),
        'ML': ('>B', 'can_mil_status'), # (Malfunction Indicator Lamp)
        'FC': ('>L', 'can_total_fuel_consumption'),
        'CI': (None, 'custom_info'),
        'AV1': ('>H', 'ain0'),
        'NC': (None, 'gsm_neighbor_cell_info'),
        'SM': ('>H' 'speed_max')
    }

    @property
    def unitId(self):
        if self._rebuild: self._build()
        return self.__unitId

    @property
    def sequenceId(self):
        if self._rebuild: self._build()
        return self.__sequenceId

    @property
    def items(self):
        if self._rebuild: self._build()
        return self.__items

    def configure(self, config):
        """
         Set supplied parameters
         @param config: dict
         @return:
        """
        if 'headerPrefix' in config:
            self.headerPrefix = config['positionReportPrefix']
        if 'customInfo' in config:
            self.customInfo = config['customInfo']
        if 'timeFormat' in config:
            self.timeFormat = int(config['timeFormat'])

    def _parseHeader(self):
        """
         Parses packet header
         @return: self
        """
        header, checksum = unpack('>HH', self._head)
        self._checksum = checksum

    def _parseBody(self):
        """
         Parses packet tail
         @return: self
        """
        seqId, unitId  = unpack('>HQ', self._body[:10])
        self.__sequenceId = seqId
        self.__unitId = str(unitId)

        # store current offset
        savedOffset = self._offset
        self._offset = 0

        buffer = self._body[10:]
        self.__items = []
        while self._offset < len(buffer):
            item = {}
            sensor = {}
            item['time'] = self.getTimeFromBuffer(buffer)
            item['time_rtc'] = self.getTimeFromBuffer(buffer)
            item['time_send'] = self.getTimeFromBuffer(buffer)
            item['longitude'] = self.readFrom('>l', buffer) / 1000000
            item['latitude'] = self.readFrom('>l', buffer) / 1000000
            item['azimuth'] = self.readFrom('>H', buffer)
            item['report_id'] = self.readFrom('>B', buffer)
            item['odometer'] = self.readFrom('>L', buffer) * 100
            item['hdop'] = self.readFrom('>H', buffer) / 10
            dInp = self.readFrom('>B', buffer)
            item['speed'] = self.readFrom('>H', buffer)
            dOut = self.readFrom('>B', buffer)
            # digital inputs and outputs
            for i in range(0, 8):
                sensor['din%d' % i] = int(bits.bitTest(dInp, i))
                sensor['dout%d' % i] = int(bits.bitTest(dOut, i))

            sensor['ain0'] = self.readFrom('>H', buffer)
            sensor['driver_id'] =\
                buffer[self._offset:].split(b'\x00')[0].decode()
            self._offset += len(sensor['driver_id']) + 1
            sensor['ext_temperature_0'] = self.readFrom('>h', buffer)
            sensor['ext_temperature_1'] = self.readFrom('>h', buffer)
            sensor['message'] =\
                buffer[self._offset:].split(b'\x00')[0].decode()
            self._offset += len(sensor['message']) + 1

            # read custom information
            fields = self.customInfo.split('%')
            for field in fields:
                if not field: continue
                if field in self.customInfoTable:
                    fmt, alias = self.customInfoTable[field]
                    if fmt:
                        sensor[alias] = self.readFrom(fmt, buffer)
                    else:
                        sensor[alias] =\
                            buffer[self._offset:].split(b'\x00')[0].decode()
                        self._offset += len(sensor[alias]) + 1
                    if alias in ['can_total_fuel_consumption']:
                        sensor[alias] /= 10
                    if alias in ['ext_battery_voltage',
                                 'int_battery_voltage']:
                        sensor[alias] *= 100

            item['sensors'] = sensor
            self.__items.append(item)

        # restore offset
        self._offset = savedOffset

    def _parseTail(self):
        """
         Parses packet tail
         @return: self
        """
        # checksum check
        if not self._isCorrectChecksum():
            raise Exception('Checksum is incorrect! ' +
                str(self.checksum) + ' (given) != ' +\
                str(self.calculateChecksum()) + ' (must be)')

        return super(PacketData, self)._parseTail()

    def calculateChecksum(self):
        """
         Returns calculated checksum
         @return: int
        """
        buffer = pack('>H', self._length) + self._body
        return crc16.Crc16.calcBinaryString(buffer, crc16.INITIAL_DF1)

    def getTimeFromBuffer(self, buffer):
        """
         Returns a datetime object read from buffer according to timeFormat
         @param buffer:
         @return: datetime
        """
        if self.timeFormat == 0:
            return datetime.utcfromtimestamp(self.readFrom('>L', buffer))
        else:
            return datetime(
                self.readFrom('>H', buffer), # year
                self.readFrom('>B', buffer), # month
                self.readFrom('>B', buffer), # day
                self.readFrom('>B', buffer), # hour
                self.readFrom('>B', buffer), # minute
                self.readFrom('>B', buffer)  # second
            )

# ---------------------------------------------------------------------------

class PacketFactory(AbstractPacketFactory):
    """
     Packet factory
    """

    def getInstance(self, data = None):
        """
          Returns a packet instance by its number
          @return: BasePacket instance
        """
        if data == None: return
        CLASS = None
        # read prefix
        pka_HeaderPrefix = PacketKeepAlive.headerPrefix
        pcr_HeaderPrefix = PacketCommandResponse.headerPrefix
        pcd_HeaderPrefix = PacketData.headerPrefix
        if 'positionReportPrefix' in self.config:
            pcd_HeaderPrefix = self.config['positionReportPrefix'].encode()
        if data[:len(pka_HeaderPrefix)] == pka_HeaderPrefix:
            CLASS = PacketKeepAlive
        elif data[:len(pcr_HeaderPrefix)] == pcr_HeaderPrefix:
            CLASS = PacketCommandResponse
        elif data[:len(pcd_HeaderPrefix)] == pcd_HeaderPrefix:
            CLASS = PacketData
        if not CLASS:
            raise Exception('Unknown packet structure')
        return CLASS(data, self.config)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest

class TestCase(unittest.TestCase):

    def setUp(self):
        from configparser import ConfigParser
        conf = ConfigParser()
        conf.optionxform = str
        conf.read('conf/serv-atrack.conf')
        section = conf['atrack.ax5']
        config = {}
        for key in section.keys():
            config[key] = section[key]

        self.factory = PacketFactory(config)
        #self.factory = PacketFactory({
        #    'positionReportPrefix': '@P',
        #    'customInfo': '%SA%MV%GQ%CE%LC%CN%RL%AT%RP' +
        #                  '%GS%DT%VN%MF%EL%TR%ET%FL%ML%FC'
        #})

    def test_keepAlivePacket(self):
        buffer = b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x01'
        packets = self.factory.getPacketsFromBuffer(buffer)
        p = packets[0]
        self.assertIsInstance(p, PacketKeepAlive)
        self.assertEqual(p.sequenceId, 1)
        self.assertEqual(p.unitId, '352964050784040')

        pka = PacketKeepAlive()
        pka.unitId = '352964050784040'
        pka.sequenceId = 15
        self.assertEqual(pka.rawData,
            b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x0f')

        pka.sequenceId = 22
        self.assertEqual(pka.rawData,
            b'\xfe\x02\x00\x01A\x04\xd8\xdd\x8f(\x00\x16')

    def test_commandResponse(self):
        packets = self.factory.getPacketsFromBuffer(b'$OK\r\n')
        p = packets[0]
        self.assertIsInstance(p, PacketCommandResponse)
        self.assertEqual(p.command, 'OK')
        self.assertEqual(p.rawData, b'$OK\r\n')

    def test_multipleCommandResponse(self):
        packets = self.factory.getPacketsFromBuffer(
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
        packets = self.factory.getPacketsFromBuffer(
            b'@P\xec\xc0\x00U\x00\x1a\x00\x01A\x04\xd8\xdd\x8f)Q\x90\xc2' +
            b'\xedQ\x90\xc2\xedQ\x94\xdc\xbc\x02>\xa5\xc0\x03SDt\x00\x00' +
            b'\x02\x00\x00\t\xcd\x00\x15\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x07\x00\x82\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x9e\x00\x00\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\xd8\x00\x00\x00\x00\x00\x00'
        )
        self.assertEqual(len(packets), 1)
        p = packets[0]
        self.assertIsInstance(p, PacketData)
        self.assertEqual(p.sequenceId, 26)
        self.assertEqual(p.unitId, '352964050784041')
        self.assertEqual(len(p.items), 1)
        i = p.items[0]
        self.assertEqual(i['time'], datetime(2013, 5, 13, 10, 39, 41))
        self.assertEqual(i['longitude'], 37.660096)
        self.assertEqual(i['latitude'], 55.78866)
        self.assertEqual(i['hdop'], 2.1)
        self.assertEqual(i['sensors']['ext_temperature_0'], 0)
        self.assertEqual(i['sensors']['ext_temperature_1'], 0)
        self.assertEqual(i['sensors']['sat_count'], 7)
        self.assertEqual(i['sensors']['can_total_fuel_consumption'], 0)

    def test_packetData2(self):
        packets = self.factory.getPacketsFromBuffer(
            b'@P\x07(\x00U\x00\x04\x00\x01A\x04\xd8\xdd\x8f)Q\x97\xd7\x7f' +
            b'Q\x97\xd7\x7fQ\x99\xcb\xc3\x02=B\xd3\x03Sjc\x01\x13\x02\x00' +
            b'\x00\x0bP\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x06\x00\x82\x0br\x8f\x1ew\x00\x00a\xaa\x14\x00\x00' +
            b'\x00\xbd\x00\x00\x08\x00\x00\x00\x00\x00\x00\xff\xd8\x00\x00' +
            b'\x00\x00\x00\x00'
        )
        self.assertEqual(len(packets), 1)
        p = packets[0]
        
        self.assertIsInstance(p, PacketData)
        self.assertEqual(p.sequenceId, 4)
        self.assertEqual(p.unitId, '352964050784041')
        self.assertEqual(len(p.items), 1)
