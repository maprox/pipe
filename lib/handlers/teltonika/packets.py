# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika packets
@copyright 2012, Maprox LLC
'''

from datetime import datetime
from struct import *
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
    _fmtHeader = '>L'   # header format
    _fmtLength = '>L'   # packet length format
    _fmtChecksum = '>L' # checksum format
    _AvlDataArray = None

    @property
    def AvlDataArray(self):
        if self._rebuild: self._build()
        return self._AvlDataArray

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

    def calculateChecksum(self):
        """
         Calculates CRC (CRC-16 Modbus)
         @param buffer: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        return crc16.Crc16.calcBinaryString(self._body, crc16.INITIAL_DF1)

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
    _params = None
    _ioElement = None

    @property
    def params(self):
        if self._rebuild: self._build()
        return self._params

    @params.setter
    def params(self, value):
        self._params = value
        self._rebuild = True

    @property
    def ioElement(self):
        if self._rebuild: self._build()
        return self._ioElement

    @ioElement.setter
    def ioElement(self, value):
        self._ioElement = value
        self._rebuild = True

    def convertCoordinate(self, coord):
        result = str(coord)
        result = result[:2] + '.' + result[2:]
        return float(result)

    def _parseBody(self):
        """
         Parses packet's head
         @return: self
        """
        super(AvlData, self)._parseBody()
        self._body = self._rawData

        self._params = {}
        self._params['time'] = datetime.utcfromtimestamp(
            self.readFrom('>Q') / 1000)
        self._params['priority'] = self.readFrom('>B')
        self._params['longitude'] = self.convertCoordinate(self.readFrom('>l'))
        self._params['latitude'] = self.convertCoordinate(self.readFrom('>l'))
        self._params['altitude'] = self.readFrom('>H')
        self._params['azimuth'] = self.readFrom('>H')
        self._params['satellitescount'] = self.readFrom('>B')
        self._params['speed'] = self.readFrom('>H')

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
      Item of data packet of teltonika fmxxxx configuration packet
    """
    _fmtLength = '>H'   # packet length format
    _packetId = 0
    _params = None
    _paramsMap = None

    @property
    def packetId(self):
        if self._rebuild: self._build()
        return self._packetId

    @packetId.setter
    def packetId(self, value):
        self._packetId = value
        self._rebuild = True

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        self._params = value
        self._rebuild = True

    def _parseBody(self):
        """
         @return:
        """
        self._offset = len(self._head)
        self._packetId = self.readFrom('>B')
        paramCount = self.readFrom('>H')
        self._params = TeltonikaConfigurationParam.getParamsFromBuffer(
            self._body[3:], paramCount)
        self._paramsMap = {}
        for param in self._params:
            self._paramsMap[param.id] = param

    def getParamById(self, id):
        """
         Returns parameter by its identifier
         @param id: int - param id
         @return: str
        """
        if (self._paramsMap is not None) and (id in self._paramsMap):
            return self._paramsMap[id]
        return None

    def addParamInstance(self, param):
        """
         Adds a param instance to the configuration packet
         @param param: TeltonikaConfigurationParam instance
         @return: self
        """
        if self._params is None:
            self._params = []
        self._params.append(param)
        self._rebuild = True
        return self

    def addParam(self, id, value):
        """
         Adds a param by its id and value
         @param id: int
         @param value: str
         @return: self
        """
        return self.addParamInstance(
            TeltonikaConfigurationParam.getInstance(id, value))

    def _buildHead(self):
        """
         Builds body of the packet
         @return: str
        """
        if self._params is None:
            self._params = []
        self._body = b''
        self._body += pack('>B', self._packetId)
        self._body += pack('>H', len(self._params))
        for param in self._params:
            self._body += param.rawData
        return super(TeltonikaConfiguration, self)._buildHead()

    def isCorrectAnswer(self, buffer):
        """
         Returns true if tracker answer is correct
         @param buffer: str
         @return: True if answer is correct
        """
        if len(buffer) < 3:
            return False
        packetId = unpack('>B', buffer[:1])[0]
        packetLength = unpack('>H', buffer[1:3])[0]
        return (packetId == self.packetId) and \
               (packetLength == self.length)

# ---------------------------------------------------------------------------

class TeltonikaConfigurationParam(BasePacket):
    """
      Item of data packet of naviset messaging protocol
    """
    _fmtHeader = '>H'   # packet length format
    _fmtLength = '>H'   # packet length format

    @property
    def id(self):
        if self._rebuild: self._build()
        return self._header

    @id.setter
    def id(self, value):
        self._header = value
        self._rebuild = True

    @property
    def value(self):
        if self._rebuild: self._build()
        return self._body.decode()

    @value.setter
    def value(self, value):
        self._body = str(value).encode()
        self._rebuild = True

    @classmethod
    def getParamsFromBuffer(cls, buffer = None, itemsCount = None):
        """
         Returns an array of TeltonikaConfigurationParam instances from data
         @param buffer: Input binary data
         @param itemsCount: Count of items in the buffer
         @return: array of TeltonikaConfigurationParam instances (empty array if no param found)
        """
        params = []
        index = 0
        while (itemsCount is None) or (index < itemsCount):
            item = TeltonikaConfigurationParam(buffer)
            buffer = item.rawDataTail
            params.append(item)
            if (len(buffer) == 0): break
            index += 1
        return params

    @classmethod
    def getInstance(cls, id, value):
        instance = cls()
        instance.id = id
        instance.value = value
        return instance

# ---------------------------------------------------------------------------
# Configuration param identifier constants                    # DEFAULT VALUE

CFG_DEEP_SLEEP_MODE = 1000
CFG_ANALOG_INPUT_VALUE_RANGE = 1001
CFG_STOP_DETECTION_SOURCE = 1002                              # 0
CFG_STOP_DETECTION_VAL_IGNITION = 0
CFG_STOP_DETECTION_VAL_MOVEMENT_SENSOR = 1
CFG_STOP_DETECTION_VAL_GPS = 2
CFG_SORTING = 1010                                            # 0
CFG_SORTING_DESC = 0
CFG_SORTING_ASC = 1
CFG_ACTIVE_DATA_LINK_TIMEOUT = 1011
CFG_UNKNOWN_PARAM_1012 = 1012
CFG_GPRS_CONTENT_ACTIVATION = 1240
CFG_APN_NAME = 1242
CFG_APN_USERNAME = 1243
CFG_APN_PASSWORD = 1244
CFG_TARGET_SERVER_IP_ADDRESS = 1245
CFG_TARGET_SERVER_PORT = 1246
CFG_PROTOCOL = 1247
CFG_SMS_LOGIN = 1252
CFG_SMS_PASSWORD = 1253
CFG_SMS_DATA_SENDING_SETTINGS = 1250
CFG_SMS_DATA_SEND_WEEK_TIME_SCHEDULE = 1273
CFG_AUTHORIZED_PHONE_NUMBER_0 = 1260
CFG_AUTHORIZED_PHONE_NUMBER_1 = 1261
CFG_AUTHORIZED_PHONE_NUMBER_2 = 1262
CFG_AUTHORIZED_PHONE_NUMBER_3 = 1263
CFG_AUTHORIZED_PHONE_NUMBER_4 = 1264
CFG_AUTHORIZED_PHONE_NUMBER_5 = 1265
CFG_AUTHORIZED_PHONE_NUMBER_6 = 1266
CFG_AUTHORIZED_PHONE_NUMBER_7 = 1267
CFG_AUTHORIZED_PHONE_NUMBER_8 = 1268
CFG_AUTHORIZED_PHONE_NUMBER_9 = 1269
CFG_OPERATOR_LIST = 1271
# VEHICLE ON STOP
CFG_VEHICLE_ON_STOP_MIN_PERIOD = 1540                         # 600
CFG_VEHICLE_ON_STOP_MIN_SAVED_RECORDS = 1543                  # 10
CFG_VEHICLE_ON_STOP_SEND_PERIOD = 1544                        # 600
CFG_VEHICLE_ON_STOP_GPRS_WEEK_TIME = 1545
# VEHICLE MOVING
CFG_VEHICLE_MOVING_MIN_PERIOD = 1550                          # 1200
CFG_VEHICLE_MOVING_MIN_DISTANCE = 1551                        # 1000
CFG_VEHICLE_MOVING_MIN_ANGLE = 1552                           # 30
CFG_VEHICLE_MOVING_MIN_SAVED_RECORDS = 1553                   # 10
CFG_VEHICLE_MOVING_SEND_PERIOD = 1554                         # 600
CFG_VEHICLE_MOVING_GPRS_WEEK_TIME = 1555
# ROAMING VEHICLE ON STOP
CFG_ROAMING_VEHICLE_ON_STOP_MIN_PERIOD = 1560
CFG_ROAMING_VEHICLE_ON_STOP_MIN_SAVED_RECORDS = 1563
CFG_ROAMING_VEHICLE_ON_STOP_SEND_PERIOD = 1564
CFG_ROAMING_VEHICLE_ON_STOP_GPRS_WEEK_TIME = 1565
# ROAMING VEHICLE MOVING
CFG_ROAMING_VEHICLE_MOVING_MIN_PERIOD = 1570
CFG_ROAMING_VEHICLE_MOVING_MIN_DISTANCE = 1571
CFG_ROAMING_VEHICLE_MOVING_MIN_ANGLE = 1572
CFG_ROAMING_VEHICLE_MOVING_MIN_SAVED_RECORDS = 1573
CFG_ROAMING_VEHICLE_MOVING_SEND_PERIOD = 1574
CFG_ROAMING_VEHICLE_MOVING_GPRS_WEEK_TIME = 1575
# UNKNOWN NETWORK VEHICLE ON STOP
CFG_UNKNOWN_NETWORK_VEHICLE_ON_STOP_MIN_PERIOD = 1580
CFG_UNKNOWN_NETWORK_VEHICLE_ON_STOP_MIN_SAVED_RECORDS = 1583
CFG_UNKNOWN_NETWORK_VEHICLE_ON_STOP_SEND_PERIOD = 1584
CFG_UNKNOWN_NETWORK_VEHICLE_ON_STOP_GPRS_WEEK_TIME = 1585
# UNKNOWN NETWORK VEHICLE MOVING
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_MIN_PERIOD = 1590
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_MIN_DISTANCE = 1591
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_MIN_ANGLE = 1592
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_MIN_SAVED_RECORDS = 1593
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_SEND_PERIOD = 1594
CFG_UNKNOWN_NETWORK_VEHICLE_MOVING_GPRS_WEEK_TIME = 1595
# FEATURES PARAMETERS
CFG_DIGITAL_OUTPUT_1_USAGE_SCENARIOS = 1600
CFG_MAX_ACCELERATION_FORCE = 1602
CFG_MAX_BREAKING_FORCE = 1603
CFG_MAX_CORNERING_ANGLE = 1604
CFG_MAX_ALLOWED_SPEED = 1605
CFG_DIGITAL_OUTPUT_2_USAGE_SCENARIOS = 1601
CFG_TRIP = 1280
CFG_START_SPEED = 1281
CFG_IGNITION_OFF_TIMEOUT = 1282
CFG_TRIP_CONTINUOUS_DISTANCE_COUNTING = 1283
# GEOFENCING
CFG_FRAME_BORDER = 1020
CFG_GEOFENCE_ZONE_1_SHAPE = 1030
CFG_GEOFENCE_ZONE_1_PRIORITY = 1031
CFG_GEOFENCE_ZONE_1_GENERATE_EVENT = 1032
CFG_GEOFENCE_ZONE_1_LONGITUDE_X_1 = 1033
CFG_GEOFENCE_ZONE_1_LATITUDE_Y_1 = 1034
CFG_GEOFENCE_ZONE_1_LONGITUDE_X_2 = 1035
CFG_GEOFENCE_ZONE_1_LATITUDE_Y_2 = 1036
# ... SKIPPED ZONE_2 (104*), 3 (105*), 4 (106*), 5 (107*)
CFG_AUTOGEOFENCING_ENABLED = 1101
CFG_AUTOGEOFENCING_ACTIVATION_TIMEOUT = 1102
CFG_AUTOGEOFENCING_DEACTIVATE_BY = 1100
CFG_AUTOGEOFENCING_EVENT_PRIORITY = 1103
CFG_AUTOGEOFENCING_EVENT_GENERATING = 1104
CFG_AUTOGEOFENCING_RADIUS = 1105
# iButton List (ID=1610-1659)
CFG_IBUTTON_FIRST = 1610
CFG_IBUTTON_LAST = 1659

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
          Returns a packet instance by its number
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
        self.assertEqual(item.params['time'].
            strftime('%Y-%m-%dT%H:%M:%S.%f'), '2007-07-25T06:46:38.335000')
        self.assertEqual(item.params['priority'], 0)
        self.assertEqual(item.params['longitude'], 25.3032016)
        self.assertEqual(item.params['latitude'], 54.7146368)
        self.assertEqual(item.params['altitude'], 111)
        self.assertEqual(item.params['azimuth'], 214)
        self.assertEqual(item.params['satellitescount'], 4)
        self.assertEqual(item.params['speed'], 4)
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
               b'\x03\x00\x01\x46\x00\x00\x01\x5d\x00\x01\x00\x00\xcf\x77'
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
               b'\x30\x04\x28\x00\x01\x30\x0c\xbd\x00\x0c+37044444444'
        packet = TeltonikaConfiguration(data)
        self.assertEqual(packet.length, 146)
        self.assertEqual(packet.packetId, 140)
        self.assertEqual(len(packet.params), 26)
        self.assertEqual(packet.getParamById(12), None)
        param = packet.getParamById(3261)
        self.assertEqual(param.value, '+37044444444')
        packet.addParam(12, 'SAMPLE')
        newParam = TeltonikaConfigurationParam()
        newParam.id = 255
        newParam.value = 'WELCOME TO THE TELTONIKA!'
        packet.addParamInstance(newParam)
        self.assertEqual(newParam.rawData,
            b'\x00\xff\x00\x19WELCOME TO THE TELTONIKA!')
        self.assertEqual(len(packet.params), 28)
        self.assertEqual(packet.length, 185)

    def test_createConfigurationPacket(self):
        packet = TeltonikaConfiguration()
        self.assertIsNone(packet.rawData)
        self.assertEqual(packet.length, 0)
        packet.addParam(12, 'SAMPLE')
        self.assertGreater(packet.length, 0)
        packet.packetId = 15
        packet.addParam(1024, '1024')
        self.assertEqual(packet.rawData,
            b'\x00\x15\x0F\x00\x02\x00\x0c\x00\x06SAMPLE\x04\x00\x00\x041024')
        self.assertTrue(packet.isCorrectAnswer(b'\x0F\x00\x15'))

    def test_teltonikaData(self):
        data = b'\x00\x00\x00\x00\x00\x00\x02\xf1\x08\x19\x00\x00\x01<' +\
               b'\x95@\xd8\xbe\x00\x16BE\xe0!#,\xc0\x01#\x00\x00\x07\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x957\xadz\x00' +\
               b'\x16BE\xe0!#,\xc0\x01\x1c\x00\x00\x07\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x01<\x95\'\x19\xa6\x00\x16B=' +\
               b'\xa0!#.\xc0\x00\xf6\x00\x00\x08\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x95\x1d\xeff\x00\x16B=\xa0!#.\xc0' +\
               b'\x01\x07\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x95\x14\xc7\xa6\x00\x16B=\xa0!#.\xc0\x00' +\
               b'\xe4\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x95\x0b\x9cb\x00\x16B=\xa0!#.\xc0\x00\xbe\x00' +\
               b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x95\x02t\xa2\x00\x16B=\xa0!#.\xc0\x00\xf1\x00\x00\x06' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xf9L' +\
               b'\xe2\x00\x16B=\xa0!#.\xc0\x00\xf0\x00\x00\x06\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xf0%"\x00\x16' +\
               b'B=\xa0!#.\xc0\x01\x0b\x00\x00\x08\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x01<\x94\xe6\xfa\x10\x00\x16B=\xa0' +\
               b'!#.\xc0\x00\xf3\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x01<\x94\xdd\xd2P\x00\x16B=\xa0!#.\xc0\x00' +\
               b'\xef\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x01<\x94\xd4\xaa\x90\x00\x16B=\xa0!#.\xc0\x00\xef' +\
               b'\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94\xcb\x82\xd0\x00\x16B=\xa0!#.\xc0\x00\xd3\x00' +\
               b'\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x94\xc2Z\xfc\x00\x16B=\xa0!#.\xc0\x00\xdf\x00\x00\x08' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xb93<' +\
               b'\x00\x16B=\xa0!#.\xc0\x00\xe1\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x01<\x94\xb0\x0br\x00\x16' +\
               b'B4\x80!#(\xc0\x00\xf6\x00\x00\t\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x94\xa6\xe3\xb2\x00\x16B4\x80!#(' +\
               b'\xc0\x00\xf0\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x01<\x94\x9c)\xcc\x00\x16B8\x80!#6\x80\x00' +\
               b'\xf1\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94\x93\x02\x0c\x00\x16B8\x80!#6\x80\x01\x0f\x00' +\
               b'\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<' +\
               b'\x94\x89\xdaL\x00\x16B8\x80!#6\x80\x00\xbf\x00\x00\t\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94y\x82\xbe' +\
               b'\x00\x16B;\xe0!#1\x00\x00\xb0\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x01<\x94pZ\xfe\x00\x16B;' +\
               b'\xe0!#1\x00\x00\xe0\x00\x00\x07\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x01<\x94g/t\x00\x16B;\xe0!#1\x00\x00' +\
               b'\xfe\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x01<\x94^\x03\xf4\x00\x16B;\xe0!#1\x00\x00\xfa\x00\x00' +\
               b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01<\x94T' +\
               b'\xdc4\x00\x16B7\x80!#2@\x01\x18\x00\x00\x08\x00\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x19\x00\x00\x1bb'
        packets = PacketFactory.getPacketsFromBuffer(data)
        self.assertEqual(len(packets), 1)
        packet = packets[0]
        self.assertTrue(isinstance(packet, PacketData))
        avl = packet.AvlDataArray
        self.assertEqual(len(avl.items), 25)
        self.assertEqual(avl.codecId, 8)
        item = avl.items[0]
        self.assertEqual(item.ioElement, {
            'eventIoId': 0,
            'items': []
        })

