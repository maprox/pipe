# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Galileo tags
@copyright 2012, Maprox LLC
'''

import time
from datetime import datetime
from struct import unpack, pack, calcsize
import lib.bits as bits

# ---------------------------------------------------------------------------

class Tag(object):
    """
     Default galileo protocol tag
    """

    # protected
    _rawdatalength = 0

    # private
    __rawdata = None
    __value = None
    __convert = True

    @classmethod
    def getNumber(cls):
        """
         Returns this tag number
        """
        result = cls.__name__[3:]
        try:
            result = int(result)
        except:
            pass
        return result

    @classmethod
    def getRawDataLength(cls):
        """
         Returns this tag length.
         If this method returns negative number (for example -2),
         it means that for calculating the length of data of this tag we need
         to retrieve next 2 bytes.
        """
        return cls._rawdatalength

    @classmethod
    def getClass(cls, number):
        """
         Returns a tag class by number
        """
        clsname = 'Tag' + str(number)
        if not clsname in globals(): 
            return None
        return globals()[clsname]

    @classmethod
    def getInstance(cls, number, data = None):
        """
          Returns a tag instance by its number
        """
        CLASS = cls.getClass(number)
        if not CLASS:
            raise Exception('Tag %s is not found' % number)
        return CLASS(data)

    def __init__(self, data = None):
        """
         Constructor
        """
        if isinstance(data, bytes):
            self.setRawData(data)
        else:
            self.setValue(data)

    def getRawData(self):
        """
         Returns tag raw data
        """
        return self.__rawdata

    def setRawData(self, rawdata):
        """
         Sets raw data
        """
        self.__rawdata = rawdata
        self.__convert = True

    def setValue(self, value):
        """
         Sets value for current tag
        """
        self.__value = value
        self.__rawdata = self.getRawDataFromValue(value)
        self.__convert = False

    def getValue(self):
        """
         Returns current value
        """
        if self.__convert:
            self.__value = self.getValueFromRawData(self.getRawData())
            self.__convert = False
        return self.__value

    def getValueFromRawData(self, rawdata):
        """
         Converts value to raw data
        """
        return rawdata

    def getRawDataFromValue(self, value):
        """
         Converts rawData to value
        """
        return value

    def getRawTag(self):
        """
         Returns raw tag value for appending to stream
        """
        return pack('<B', self.getNumber()) + self.getRawData()

    def __str__(self):
        return str(self.getValue())

# ---------------------------------------------------------------------------

class TagNumber(Tag):
    """
     Tag with integer data
    """

    # number size in bytes
    _packfmt = "<B"

    @classmethod
    def getRawDataLength(cls):
        """
         Returns this tag length.
         If this method returns negative number (for example -2),
         it means that for calculating the length of data of this tag we need
         to retrieve next 2 bytes.
        """
        return calcsize(cls._packfmt)

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        return unpack(self._packfmt, rawdata)[0]

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        return pack(self._packfmt, value)

# ---------------------------------------------------------------------------

class TagNumberByte(TagNumber):
    """
     Tag with one byte of data
    """
    _packfmt = "<B"

# ---------------------------------------------------------------------------

class TagNumberShort(TagNumber):
    """
     Tag with 2 bytes integer
    """
    _packfmt = "<H"

# ---------------------------------------------------------------------------

class TagNumberLong(TagNumber):
    """
     Tag with 4 bytes integer
    """
    _packfmt = "<L"

# ---------------------------------------------------------------------------

class TagDateTime(TagNumberLong):
    """
     Tag with timestamp data
    """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        timestamp = super(TagDateTime, self).getValueFromRawData(rawdata)
        return datetime.utcfromtimestamp(timestamp)

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        timestamp = time.mktime(value.timetuple())
        return super(TagDateTime, self).getRawDataFromValue(timestamp)

# ---------------------------------------------------------------------------

class TagString(Tag):
    """
     Tag with string data
    """

    def getValueFromRawData(self, rawdata):
        """
         Converts data to raw data
        """
        if (rawdata == None): return None
        return rawdata.decode()

    def getRawDataFromValue(self, value):
        """
         Converts data to raw data
        """
        if (value == None): return None
        return value.encode()

# ---------------------------------------------------------------------------

class Tag0(Tag):
    """ 0x00: ByteString (for example JPG photo from camera)"""

# ---------------------------------------------------------------------------

class Tag1(TagNumberByte):
    """ 0x01: Firmware """

# ---------------------------------------------------------------------------

class Tag2(TagNumberByte):
    """ 0x02: Software """

# ---------------------------------------------------------------------------

class Tag3(TagString):
    """ 0x03: IMEI """
    _rawdatalength = 15

# ---------------------------------------------------------------------------

class Tag4(TagNumberShort):
    """ 0x04: Code """

# ---------------------------------------------------------------------------

class Tag16(TagNumberShort):
    """ 0x10: Archive number """

# ---------------------------------------------------------------------------

class Tag32(TagDateTime):
    """ 0x20: Timestamp """

# ---------------------------------------------------------------------------

class Tag48(TagNumber):
    """ 0x30: Satellites count, Correctness, Latitude, Longitude """
    _packfmt = "<Bll"

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        (satcor, latitude, longitude) = unpack(self._packfmt, rawdata)
        correctness = satcor >> 4
        satellitescount = satcor % 128
        return {
          'satellitescount': satellitescount,
          'correctness': correctness,
          'latitude': latitude / 1000000,
          'longitude': longitude / 1000000
        }

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        lat = value['latitude'] if 'latitude' in value else 0
        lon = value['longitude'] if 'longitude' in value else 0
        cor = value['correctness'] if 'correctness' in value else 0
        sat = value['satellitescount'] if 'satellitescount' in value else 0
        satcor = int(sat + (cor << 4))
        return pack(self._packfmt, satcor,
          int(lat * 1000000), int(lon * 1000000))


# ---------------------------------------------------------------------------

class Tag51(TagNumber):
    """ 0x33: Speed, Azimuth """
    _packfmt = "<HH"

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        (speed, azimuth) = unpack(self._packfmt, rawdata)
        return {
          'speed': speed / 10,
          'azimuth': azimuth / 10
        }

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        speed = value['speed'] if 'speed' in value else 0
        azimuth = value['azimuth'] if 'azimuth' in value else 0
        return pack(self._packfmt, int(speed * 10), int(azimuth * 10))

# ---------------------------------------------------------------------------

class Tag52(TagNumberShort):
    """ 0x34: Altitude """

# ---------------------------------------------------------------------------

class Tag53(TagNumberByte):
    """ 0x35: HDOP """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        result = super(Tag53, self).getValueFromRawData(rawdata)
        return result / 10

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        result = int(value * 10)
        return super(Tag53, self).getRawDataFromValue(result)

# ---------------------------------------------------------------------------

class Tag64(TagNumberShort):
    """ 0x40: Status """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        r = super(Tag64, self).getValueFromRawData(rawdata)
        return {
          'movementsensor':   bits.bitValue(r,  0),
          'criticalangle':    bits.bitValue(r,  1),
          'nosimcard':        bits.bitValue(r,  3),
          'ingeofence':       bits.bitValue(r,  4),
          'extbattery_low':   bits.bitValue(r,  5),
          'gpsantenna':   1 - bits.bitValue(r,  6),
          'badbusvoltage':    bits.bitValue(r,  7),
          'badextvoltage':    bits.bitValue(r,  8),
          'acc':              bits.bitValue(r,  9),
          'crashvibration':   bits.bitValue(r, 10),
          'glonass':          bits.bitValue(r, 11),
          'signalquality':    bits.bitValue(r, 12) \
            + (2 * bits.bitValue(r, 13)),
          'alarmmodeon':      bits.bitValue(r, 14),
          'sos':              bits.bitValue(r, 15)
        }

    @classmethod
    def bitSet(cls, result, offset, value, varname):
        """
         Set bit value for number
        """
        return bits.bitSetValue(result, offset, value[varname] \
          if varname in value else 0)

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        r = 0
        r = self.bitSet(r, 0, value, 'movementsensor')
        r = self.bitSet(r, 1, value, 'criticalangle')
        r = self.bitSet(r, 3, value, 'nosimcard')
        r = self.bitSet(r, 4, value, 'ingeofence')
        r = self.bitSet(r, 5, value, 'extbattery_low')
        r = self.bitSet(r, 6, value, 'gpsantenna')
        r = self.bitSet(r, 7, value, 'badbusvoltage')
        r = self.bitSet(r, 8, value, 'badextvoltage')
        r = self.bitSet(r, 9, value, 'acc')
        r = self.bitSet(r, 10, value, 'crashvibration')
        r = self.bitSet(r, 11, value, 'glonass')
        r = self.bitSet(r, 12, value, 'signalquality')
        if 'alarmmodeon' in value:
            r = bits.bitSetValue(r, 13, value['alarmmodeon'] % 2)
            r = bits.bitSetValue(r, 14, value['alarmmodeon'] >> 1)
        r = self.bitSet(r, 15, value, 'sos')
        return super(Tag64, self).getRawDataFromValue(r)

# ---------------------------------------------------------------------------

class Tag65(TagNumberShort):
    """ 0x41: Voltage """

# ---------------------------------------------------------------------------

class Tag66(TagNumberShort):
    """ 0x42: Accumulator voltage """

# ---------------------------------------------------------------------------

class Tag67(TagNumber):
    """ 0x43: Terminal temperature """
    _packfmt = "<b"

# ---------------------------------------------------------------------------

class Tag68(TagNumberLong):
    """ 0x44: Acceleration """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        r = super(Tag68, self).getValueFromRawData(rawdata)
        return {
          'X': r % 1024,
          'Y': (r >> 10) % 1024,
          'Z': (r >> 20) % 1024
        }

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        r = value['Z'] if 'Z' in value else 0
        r <<= 10
        r += value['Y'] if 'Y' in value else 0
        r <<= 10
        r += value['X'] if 'X' in value else 0
        return super(Tag68, self).getRawDataFromValue(r)

# ---------------------------------------------------------------------------

class Tag69(TagNumberShort):
    """ 0x45: Digital output """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        r = super(Tag69, self).getValueFromRawData(rawdata)
        res = {}
        for idx in range(16):
            varname = 'do' + str(idx)
            res[varname] = bits.bitValue(r, idx)
        return res

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        r = 0
        for idx in range(16):
            varname = 'do' + str(idx)
            bits.bitSetValue(r, idx, value[varname] \
              if varname in value else 0)
        return super(Tag69, self).getRawDataFromValue(r)

# ---------------------------------------------------------------------------

class Tag70(TagNumberShort):
    """ 0x46: Digital input """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        r = super(Tag70, self).getValueFromRawData(rawdata)
        res = {}
        for idx in range(16):
            varname = 'di' + str(idx)
            res[varname] = bits.bitValue(r, idx)
        return res

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        r = 0
        for idx in range(16):
            varname = 'di' + str(idx)
            bits.bitSetValue(r, idx, value[varname] \
              if varname in value else 0)
        return super(Tag70, self).getRawDataFromValue(r)

# ---------------------------------------------------------------------------

class Tag80(TagNumberShort):
    """ 0x50: Analog input 0"""

# ---------------------------------------------------------------------------

class Tag81(TagNumberShort):
    """ 0x51: Analog input 1"""

# ---------------------------------------------------------------------------

class Tag82(TagNumberShort):
    """ 0x52: Analog input 2"""

# ---------------------------------------------------------------------------

class Tag83(TagNumberShort):
    """ 0x53: Analog input 3"""

# ---------------------------------------------------------------------------

class Tag88(TagNumberShort):
    """ 0x58: RS232 0 """

# ---------------------------------------------------------------------------

class Tag89(TagNumberShort):
    """ 0x59: RS232 1 """

# ---------------------------------------------------------------------------

class TagThermometer(TagNumberShort):
    """ 0x70: Thermometer tag """
    _packfmt = "<BB"

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        (identifier, temperature) = unpack(self._packfmt, rawdata)
        return {
          'identifier': identifier,
          'temperature': temperature
        }

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        identifier = value['identifier'] if 'identifier' in value else 0
        temperature = value['temperature'] if 'temperature' in value else 0
        return pack(self._packfmt, identifier, temperature)

# ---------------------------------------------------------------------------

class Tag112(TagThermometer):
    """ 0x70: Thermometer 0 """

# ---------------------------------------------------------------------------

class Tag113(TagThermometer):
    """ 0x71: Thermometer 1 """

# ---------------------------------------------------------------------------

class Tag114(TagThermometer):
    """ 0x72: Thermometer 2 """

# ---------------------------------------------------------------------------

class Tag115(TagThermometer):
    """ 0x73: Thermometer 3 """

# ---------------------------------------------------------------------------

class Tag116(TagThermometer):
    """ 0x74: Thermometer 4 """

# ---------------------------------------------------------------------------

class Tag117(TagThermometer):
    """ 0x75: Thermometer 5 """

# ---------------------------------------------------------------------------

class Tag118(TagThermometer):
    """ 0x76: Thermometer 6 """

# ---------------------------------------------------------------------------

class Tag119(TagThermometer):
    """ 0x77: Thermometer 7 """

# ---------------------------------------------------------------------------

class Tag144(TagNumberLong):
    """ 0x90: iButton 1 """

# ---------------------------------------------------------------------------

class Tag192(TagNumberLong):
    """ 0xc0: FMS-Standard. Fuel from start """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        return super(Tag192, self).getValueFromRawData(rawdata) / 2

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        return super(Tag192, self).getRawDataFromValue(int(value * 2))

# ---------------------------------------------------------------------------

class Tag193(TagNumberLong):
    """ 0xc1: CAN: Fuel percent, Temperature, RPM """

    _packfmt = "<BBH"

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        (fuelpercent, temperature, rpm) = unpack(self._packfmt, rawdata)
        return {
          'fuelpercent': int(fuelpercent * 0.4),
          'temperature': int(temperature - 40),
          'rpm': int(rpm * 0.125)
        }

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        fuelpercent = value['fuelpercent'] if 'fuelpercent' in value else 0
        temperature = value['temperature'] if 'temperature' in value else 0
        rpm = value['rpm'] if 'rpm' in value else 0
        return pack(self._packfmt,
          int(fuelpercent / 0.4),
          int(temperature + 40),
          int(rpm / 0.125))

# ---------------------------------------------------------------------------

class Tag194(TagNumberLong):
    """ 0xc2: FMS-Standard. Odometer """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        return super(Tag194, self).getValueFromRawData(rawdata) * 5

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        return super(Tag194, self).getRawDataFromValue(int(value / 5))

# ---------------------------------------------------------------------------

class Tag195(TagNumberLong):
    """ 0xc3: CAN_B1 """

# ---------------------------------------------------------------------------

class Tag196(TagNumberByte):
    """ 0xc4: CAN8BITR0 """

# ---------------------------------------------------------------------------

class Tag197(TagNumberByte):
    """ 0xc5: CAN8BITR1 """

# ---------------------------------------------------------------------------

class Tag198(TagNumberByte):
    """ 0xc6: CAN8BITR2 """

# ---------------------------------------------------------------------------

class Tag199(TagNumberByte):
    """ 0xc7: CAN8BITR3 """

# ---------------------------------------------------------------------------

class Tag200(TagNumberByte):
    """ 0xc8: CAN8BITR4 """

# ---------------------------------------------------------------------------

class Tag201(TagNumberByte):
    """ 0xc9: CAN8BITR5 """

# ---------------------------------------------------------------------------

class Tag202(TagNumberByte):
    """ 0xca: CAN8BITR6 """

# ---------------------------------------------------------------------------

class Tag203(TagNumberByte):
    """ 0xcb: CAN8BITR7 """

# ---------------------------------------------------------------------------

class Tag204(TagNumberByte):
    """ 0xcc: CAN8BITR8 """

# ---------------------------------------------------------------------------

class Tag205(TagNumberByte):
    """ 0xcd: CAN8BITR9 """

# ---------------------------------------------------------------------------

class Tag206(TagNumberByte):
    """ 0xce: CAN8BITR10 """

# ---------------------------------------------------------------------------

class Tag207(TagNumberByte):
    """ 0xcf: CAN8BITR11 """

# ---------------------------------------------------------------------------

class Tag208(TagNumberByte):
    """ 0xd0: CAN8BITR12 """

# ---------------------------------------------------------------------------

class Tag209(TagNumberByte):
    """ 0xd1: CAN8BITR13 """

# ---------------------------------------------------------------------------

class Tag210(TagNumberByte):
    """ 0xd2: CAN8BITR14 """

# ---------------------------------------------------------------------------

class Tag211(TagNumberLong):
    """ 0xd3: iButton 2 """

# ---------------------------------------------------------------------------

class Tag212(TagNumberLong):
    """ 0xd4: Total odometer """

# ---------------------------------------------------------------------------

class Tag213(TagNumberByte):
    """ 0xd5: iButtons state """

    def getValueFromRawData(self, rawdata):
        """
         Converts raw data to value
        """
        if (rawdata == None): return None
        r = super(Tag213, self).getValueFromRawData(rawdata)
        res = {}
        for idx in range(8):
            varname = 'ibutton' + str(idx + 1)
            res[varname] = bits.bitValue(r, idx)
        return res

    def getRawDataFromValue(self, value):
        """
         Converts value to raw data
        """
        if (value == None): return None
        r = 0
        for idx in range(8):
            varname = 'ibutton' + str(idx + 1)
            bits.bitSetValue(r, idx, value[varname] \
              if varname in value else 0)
        return super(Tag213, self).getRawDataFromValue(r)

# ---------------------------------------------------------------------------

class Tag214(TagNumberShort):
    """ 0xd6: CAN16BITR0 """

# ---------------------------------------------------------------------------

class Tag215(TagNumberShort):
    """ 0xd7: CAN16BITR1 """

# ---------------------------------------------------------------------------

class Tag216(TagNumberShort):
    """ 0xd8: CAN16BITR2 """

# ---------------------------------------------------------------------------

class Tag217(TagNumberShort):
    """ 0xd9: CAN16BITR3 """

# ---------------------------------------------------------------------------

class Tag218(TagNumberShort):
    """ 0xda: CAN16BITR4 """

# ---------------------------------------------------------------------------

class Tag219(TagNumberLong):
    """ 0xdb: CAN32BITR0 """

# ---------------------------------------------------------------------------

class Tag220(TagNumberLong):
    """ 0xdc: CAN32BITR1 """

# ---------------------------------------------------------------------------

class Tag221(TagNumberLong):
    """ 0xdd: CAN32BITR2 """

# ---------------------------------------------------------------------------

class Tag222(TagNumberLong):
    """ 0xde: CAN32BITR3 """

# ---------------------------------------------------------------------------

class Tag223(TagNumberLong):
    """ 0xdf: CAN32BITR4 """

# ---------------------------------------------------------------------------

class Tag224(TagNumberLong):
    """ 0xE0: Server command number """

# ---------------------------------------------------------------------------

class TagCompound(Tag):
    """
     Compound tag class.
     It is the tag wich raw data can be described as:
     (tag | length of data | data)
    """
    lengthfmt = '<B'

    @classmethod
    def getRawDataLength(cls):
        """
         Returns this tag length.
         If this method returns negative number (for example -2),
         it means that for calculating the length of data of this tag we need
         to retrieve next 2 bytes.
        """
        return -calcsize(cls.lengthfmt)

    def getRawTag(self):
        """
         Returns raw tag value for appending to stream
        """
        num = self.getNumber()
        data = self.getRawData()
        return pack('<B', num) + pack(self.lengthfmt, len(data)) + data

# ---------------------------------------------------------------------------

class TagCompoundString(TagCompound, TagString):
    pass

# ---------------------------------------------------------------------------

class Tag225(TagCompoundString):
    """ 0xE1: Server command """

# ---------------------------------------------------------------------------

def getLengthOfTag(number):
    """
     Returns the length of tag
    """
    CLASS = Tag.getClass(number)
    if not CLASS:
        return None
    return CLASS.getRawDataLength()


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_tagNumber(self):
        tag = Tag.getInstance('Number', b'\x34')
        tag.setValue(65)
        self.assertEqual(tag.getRawData(), b'A')
        self.assertEqual(tag.getNumber(), 'Number')

    def test_tag3(self):
        tag = Tag.getInstance(3, b'093983472983742934')
        self.assertEqual(tag.getValue(), '093983472983742934')

    def test_tag4(self):
        tag = Tag.getInstance(4, b'\x03\x04')
        self.assertEqual(tag.getValue(), 1027)

    def test_tag32(self):
        tag = Tag.getInstance(32, b'\x13\x04\xAF\x4F') # 2012-05-13 00:45:07
        self.assertEqual(tag.getValue(), datetime(2012, 5, 13, 0, 45, 7))

    def test_tag48(self):
        tag = Tag.getInstance(48, b'\x07\xC0\x0E\x32\x03\xB8\xD7\x2D\x05')
        # {'satellitescount': 7, 'correctness': 0,
        #  'latitude': 53,612224, 'longitude': 86,890424}
        tag.setValue({
          'satellitescount': 8,
          'correctness': 1,
          'latitude': 53.612224,
          'longitude': 86.890424
        })
        self.assertEqual(tag.getRawData(), b'\x18\xc0\x0e2\x03\xb8\xd7-\x05')

    def test_tag51(self):
        tag = Tag.getInstance(51)
        tag.setValue({
          'azimuth': 212.0,
          'speed': 9.2
        })
        self.assertEqual(tag.getRawData(), b'\x5C\x00\x48\x08')

    def test_tag53(self):
        tag = Tag.getInstance(53, b'\x5C')
        tag.setValue(0.2)
        self.assertEqual(tag.getRawData(), b'\x02')

    def test_tag64(self):
        tag = Tag.getInstance(64, b'\xAA\xAA')
        value = tag.getValue()
        self.assertEqual(value['crashvibration'], 0)
        self.assertEqual(value['badbusvoltage'], 1)
        self.assertEqual(value['nosimcard'], 1)
        self.assertEqual(value['signalquality'], 2)
        tag.setValue({'crashvibration': 1})
        self.assertEqual(tag.getRawData(), b'\x00\x04')

    def test_tag67(self):
        tag = Tag.getInstance(67, b'\xF5')
        self.assertEqual(tag.getValue(), -11)

    def test_tag68(self):
        tag = Tag.getInstance(68, b'\xAF\x21\x98\x15')
        value = tag.getValue()
        self.assertEqual(value['X'], 431)
        self.assertEqual(value['Y'], 520)
        self.assertEqual(value['Z'], 345)
        tag.setValue({'X': 431, 'Y': 220, 'Z': 345})
        self.assertEqual(tag.getRawData(), b'\xafq\x93\x15')

    def test_tag69(self):
        tag = Tag.getInstance(69, b'\xAF\x21')
        value = tag.getValue()
        self.assertEqual(value['do2'], 1)
        self.assertEqual(value['do11'], 0)
        self.assertEqual(value['do13'], 1)
        self.assertEqual(tag.getRawTag(), b'\x45\xAF\x21')

    def test_tag118(self):
        tag = Tag.getInstance(118, b'\x06\x10')
        value = tag.getValue()
        self.assertEqual(value['identifier'], 6)
        self.assertEqual(value['temperature'], 16)

    def test_tag193(self):
        tag = Tag.getInstance(193, b'\xFA\x72\x50\x25')
        value = tag.getValue()
        self.assertEqual(value['rpm'], 1194)
        self.assertEqual(value['fuelpercent'], 100)
        self.assertEqual(value['temperature'], 74)

    def test_tag213(self):
        tag = Tag.getInstance(213, b'\x05')
        value = tag.getValue()
        self.assertEqual(value['ibutton1'], 1)
        self.assertEqual(value['ibutton2'], 0)
        self.assertEqual(value['ibutton3'], 1)
        self.assertEqual(value['ibutton8'], 0)

    def test_tag225(self):
        tag = Tag.getInstance(225, b'SMSMSLEEEEE')
        self.assertEqual(tag.getValue(), 'SMSMSLEEEEE')
        self.assertEqual(tag.getRawDataLength(), -1)
        self.assertEqual(tag.getRawTag(), b'\xe1\x0bSMSMSLEEEEE')
        self.assertEqual(tag.lengthfmt, '<B')

    def test_tagValues(self):
        tag = Tag.getInstance(225, 'SMSMSLEEEEE')
        self.assertEqual(tag.getRawTag(), b'\xe1\x0bSMSMSLEEEEE')

        tag = Tag.getInstance(0xE0, 1)
        self.assertEqual(tag.getRawTag(), b'\xe0\x01\x00\x00\x00')
