# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset packets
@copyright 2013, Maprox LLC
'''

import time
import socket
from datetime import datetime
from struct import unpack, pack
from kernel.utils import *
import lib.bits as bits
import lib.crc16 as crc16
from lib.packets import *   
from lib.factory import AbstractPacketFactory

# ---------------------------------------------------------------------------

class NavisetBase(BasePacket):
    """
     Base class for naviset packet.
    """

    # protected properties
    _fmtChecksum = '<H' # checksum format

    def calculateChecksum(self):
        """
         Calculates CRC (CRC-16 Modbus)
         @param buffer: binary string
         @return: True if buffer crc equals to supplied crc value, else False
        """
        data = (self._head or b'') + (self._body or b'')
        return crc16.Crc16.calcBinaryString(data, crc16.INITIAL_MODBUS)

# ---------------------------------------------------------------------------

class NavisetPacket(NavisetBase):
    """
     Default naviset protocol packet
    """

    # protected properties
    _fmtHeader = None   # header format
    _fmtLength = '<H'   # packet length format

    def _parseLength(self):
        # read header and length
        head = unpack(self._fmtLength, self._head)[0]
        head = bits.bitClear(head, 15)
        head = bits.bitClear(head, 14)
        #head = bits.bitClear(head, 13)
        #head = bits.bitClear(head, 12)
        self._length = head
        self._header = head >> 14

    def _buildHead(self):
        """
         Builds rawData from object variables
         @protected
        """
        length = len(self._body)
        data = length + (self._header << 14)
        return pack(self._fmtLength, data)

# ---------------------------------------------------------------------------

class PacketNumbered(NavisetPacket):
    """
      Packet of naviset messaging protocol with device number in body
    """

    # private properties
    __deviceNumber = 0

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketNumbered, self)._parseBody()
        self.__deviceNumber = unpack("<H", self._body[:2])[0]

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
        if self._rebuild: self._build()
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
    __deviceImei = 0
    __protocolVersion = None

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketHead, self)._parseBody()
        lengthOfIMEI = 15
        self.__deviceImei = self._body[2:2 + lengthOfIMEI].decode()
        self.__protocolVersion = unpack("<B", self._body[-1:])[0]

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketHead, self)._buildBody()
        result += self.__deviceImei.encode()
        result += pack('<B', self.__protocolVersion)
        return result

    @property
    def deviceImei(self):
        if self._rebuild: self._build()
        return self.__deviceImei

    @deviceImei.setter
    def deviceImei(self, value):
        if (len(value) == 15):
            self.__deviceImei = str(value)
            self._rebuild = True

    @property
    def protocolVersion(self):
        if self._rebuild: self._build()
        return self.__protocolVersion

    @protocolVersion.setter
    def protocolVersion(self, value):
        if (0 <= value <= 0xFF):
            self.__protocolVersion = value
            self._rebuild = True

# ---------------------------------------------------------------------------

class PacketData(PacketNumbered):
    """
      Data packet of naviset messaging protocol
    """
    # private properties
    __dataStructure = 0
    __itemsData = None
    __items = None

    def __init__(self, data = None):
        """
         Constructor
         @param data: Binary data of data packet
         @return: PacketData instance
        """
        self.__items = []
        super(PacketData, self).__init__(data)

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketData, self)._parseBody()
        self.__dataStructure = unpack('<H', self._body[2:4])[0]
        self.__itemsData = self._body[4:]
        self.__items = PacketDataItem.getDataItemsFromBuffer(
            self.__itemsData,
            self.__dataStructure
        )

    def _buildBody(self):
        """
         Builds rawData from object variables
         @protected
        """
        result = super(PacketData, self)._buildBody()
        result += pack('<H', self.__dataStructure)
        return result

    @property
    def items(self):
        return self.__items

# ---------------------------------------------------------------------------

class PacketDataItem:
    """
      Item of data packet of naviset messaging protocol
    """
    # private properties
    __rawData = None
    __rawDataTail = None
    __dataStructure = 0
    __number = 0
    __params = None
    __additional = None

    # additional data sizes map
    __dsMap = {
        0: 1,
        1: 4,
        2: 1,
        3: 2,
        4: 4,
        5: 4,
        6: 4,
        7: 4,
        8: 4,
        9: 4,
        10: 6,
        11: 4,
        12: 4,
        13: 2,
        14: 4,
        15: 8
    }

    def __init__(self, data = None, ds = 0):
        """
         Constructor
         @param data: Binary data for packet item
         @param ds: Data structure word
         @return: PacketDataItem instance
        """
        super(PacketDataItem, self).__init__()
        self.__rawData = data
        self.__dataStructure = ds
        self.__params = {}
        self.__parse()

    @classmethod
    def getAdditionalDataLength(cls, ds = None):
        """
         Returns length of additional data buffer
         according to ds parameter
         @param ds: Data structure definition (2 byte)
         @return: Size of additional data buffer in bytes
        """
        # exit if dataStructure is empty
        if (ds == None) or (ds == 0):
            return 0

        size = 0
        for key in cls.__dsMap:
            if bits.bitTest(ds, key):
                size += cls.__dsMap[key]
        return size

    @classmethod
    def getDataItemsFromBuffer(cls, data = None, ds = None):
        """
         Returns an array of PacketDataItem instances from data
         @param data: Input binary data
         @return: array of PacketDataItem instances (empty array if not found)
        """
        items = []
        while True:
            item = cls(data, ds)
            data = item.rawDataTail
            items.append(item)
            if data is None or len(data) == 0: break
        return items

    def parseAdditionalData(self):
        """
         Parses additional data of the packet
         @return: dict
        """
        sensors = {}
        buffer = self.__additional
        offset = 0
        for key in range(0, 16):
            if not bits.bitTest(self.__dataStructure, key): continue
            size = self.__dsMap[key]
            data = buffer[offset:offset + size]
            offset += size
            if key == 0:
                status = unpack('<B', data)[0]
                sensors['bad_ext_voltage'] = int(bits.bitTest(status, 0))
                sensors['moving'] = int(bits.bitTest(status, 1))
                sensors['armed'] = int(bits.bitTest(status, 2))
                sensors['gsm_sim_card_1_enabled'] = int(bits.bitTest(status, 3))
                sensors['gsm_sim_card_2_enabled'] = int(bits.bitTest(status, 4))
                sensors['gsm_no_gprs_connection'] = int(bits.bitTest(status, 5))
                sensors['sat_antenna_connected'] =\
                    1 - int(bits.bitTest(status, 6))
            elif key == 1:
                vExt, vInt = unpack('<HH', data)
                sensors['ext_battery_voltage'] = vExt
                sensors['int_battery_voltage'] = vInt
            elif key == 2:
                sensors['int_temperature'] = unpack('<b', data)[0]
            elif key == 3:
                dInp, dOut = unpack('<BB', data)
                for i in range(0, 8):
                    sensors['din%d' % i] = int(bits.bitTest(dInp, i))
                    sensors['dout%d' % i] = int(bits.bitTest(dOut, i))
            elif key in range(4, 8):
                vInp1, vInp2 = unpack('<HH', data)
                index = 2 * (key - 4)
                sensors['ain%d' % index] = vInp1
                sensors['ain%d' % (index + 1)] = vInp2
            elif key in range(8, 10):
                t = unpack('<bbbb', data)
                index = 4 * (key - 8)
                for i in range(0, 4):
                    if t[i] > -100:
                        sensors['ext_temperature_%d' % (i + index)] = t[i]
            elif key == 10:
                vH, vI = unpack('<HI', data)
                sensors['ibutton_0'] = vH | (vI << 16)
            elif key == 11:
                fInp1, fInp2 = unpack('<HH', data)
                sensors['fin0'] = fInp1
                sensors['fin1'] = fInp2
            elif key == 12: # Omnicomm fuel level
                fInp1, fInp2 = unpack('<HH', data)
                sensors['omnicomm_fuel_0'] = fInp1
                sensors['omnicomm_fuel_1'] = fInp2
            elif key == 13: # Omnicomm temperature
                fInp1, fInp2 = unpack('<bb', data)
                sensors['omnicomm_temperature_0'] = fInp1
                sensors['omnicomm_temperature_1'] = fInp2
            elif key == 14: # CAN data 1
                fuel, rpm, coolantTemp = unpack('<BHb', data)
                fuelPercent = fuel * 0.4
                if fuelPercent > 100: fuelPercent = 100
                sensors['can_fuel_percent'] = fuelPercent
                sensors['can_rpm'] = rpm
                sensors['can_coolant_temperature'] = coolantTemp
            elif key == 15: # CAN data 2
                fuelConsumption, totalMileage = unpack('<LL', data)
                sensors['can_total_fuel_consumption'] = fuelConsumption * 0.5
                sensors['can_total_mileage'] = totalMileage * 5
        return sensors

    def convertCoordinate(self, coord):
        result = str(coord)
        result = result[:2] + '.' + result[2:]
        return float(result)

    def __parse(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        buffer = self.__rawData
        length = self.length
        if buffer == None: return
        if len(buffer) < length: return

        self.__number = unpack("<H", buffer[:2])[0]
        self.__params['time'] = datetime.utcfromtimestamp(
            unpack("<L", buffer[2:6])[0]) #- timedelta(hours=4)
        self.__params['satellitescount'] = unpack("<B", buffer[6:7])[0]
        self.__params['latitude'] = self.convertCoordinate(
            unpack("<L", buffer[7:11])[0])
        self.__params['longitude'] = self.convertCoordinate(
            unpack("<L", buffer[11:15])[0])
        self.__params['speed'] = unpack("<H", buffer[15:17])[0] / 10
        self.__params['azimuth'] = int(round(
            unpack("<H", buffer[17:19])[0] / 10))
        self.__params['altitude'] = unpack("<H", buffer[19:21])[0]
        self.__params['hdop'] = unpack("<B", buffer[21:22])[0] / 10
        self.__additional = buffer[22:length]
        self.__params['sensors'] = self.parseAdditionalData()

        # apply new data
        self.__rawDataTail = buffer[length:]
        self.__rawData = buffer[:length]

    @property
    def length(self):
        return 22 + self.getAdditionalDataLength(self.__dataStructure)

    @property
    def rawData(self):
        return self.__rawData

    @property
    def rawDataTail(self):
        return self.__rawDataTail

    @property
    def number(self):
        return self.__number

    @property
    def params(self):
        return self.__params

    @property
    def additional(self):
        return self.__additional

# ---------------------------------------------------------------------------

class PacketAnswer(NavisetPacket):
    """
      Data packet of naviset messaging protocol
    """

    # private properties
    _number = 0

    @property
    def command(self):
        if self._rebuild: self._build()
        return self._number

    def get_dict(self):
        params_dict = {}
        return params_dict

    def get_parameters_string(self):
        s = ''
        return s

    @classmethod
    def getInstance(cls, data = None):
        CLASS = None
        if data:
            command = unpack('<B', data[2:3])[0]
            CLASS = getAnswerClassByNumber(command)
        return CLASS

# ---------------------------------------------------------------------------

IMAGE_ANSWER_CODE_SIZE = 0
IMAGE_ANSWER_CODE_DATA = 1
IMAGE_ANSWER_CODE_CAMERA_NOT_FOUND = 2
IMAGE_ANSWER_CODE_CAMERA_IS_BUSY = 3

class PacketAnswerCommandChangeDeviceNumber(PacketAnswer): 
    _number = 2
class PacketAnswerCommandChangeDevicePassword(PacketAnswer): 
    _number = 3
class PacketAnswerCommandSetGprsParams(PacketAnswer): 
    _number = 4
class PacketAnswerCommandAddRemoveKeyNumber(PacketAnswer): 
    _number = 6
class PacketAnswerCommandAddRemovePhoneNumber(PacketAnswer): 
    _number = 8
class PacketAnswerCommandProtocolTypeStructure(PacketAnswer): 
    _number = 9
class PacketAnswerCommandFiltrationDrawingParameters(PacketAnswer): 
    _number = 11
class PacketAnswerCommandConfigureInputs(PacketAnswer): 
    _number = 12
class PacketAnswerCommandConfigureOutputs(PacketAnswer): 
    _number = 13
class PacketAnswerCommandTemporarySecurityParameters(PacketAnswer): 
    _number = 15
class PacketAnswerCommandRemoveTrackFromBuffer(PacketAnswer): 
    _number = 16
class PacketAnswerCommandVoiceConnectionParameters(PacketAnswer): 
    _number = 17
class PacketAnswerCommandRestart(PacketAnswer): 
    _number = 18
class PacketAnswerCommandSoftwareUpgrade(PacketAnswer): 
    _number = 19
class PacketAnswerCommandSwitchToNewSim(PacketAnswer): 
    _number = 23
class PacketAnswerCommandSwitchToConfigurationServer(PacketAnswer): 
    _number = 24
class PacketAnswerCommandAllowDisallowSimAutoswitching(PacketAnswer): 
    _number = 25




class PacketAnswerCommonAnswerUnknownIdentifier(PacketAnswer):
    """
    Common answer, sent when command identifier is unknown
    """ 
    _number = 250

    def get_parameters_string(self):
        return "Command identifier is unknown"

class PacketAnswerCommonAnswerDataIntegrityError(PacketAnswer):
    """
    Common answer, sent when data integrity error happened
    """ 
    _number = 251

    def get_parameters_string(self):
        return "Data integrity error/wrong parameters number"

class PacketAnswerCommonAnswerCommandReceivedProcessed(PacketAnswer):
    """
    Common answer, sent when command successfully received and processed
    """ 
    _number = 252

    def get_parameters_string(self):
        return "Command was successfully received and processed"

class PacketAnswerCommonAnswerCommandProcessingError(PacketAnswer):
    """
    Common answer, sent when error during command processing happened
    """ 
    _number = 253

    def get_parameters_string(self):
        s = "Error during command processing"
        return s

class PacketAnswerCommandGetImei(PacketAnswer):
    """
     Answer on CommandGetImei
    """
    _number = 1

    __imei = "000000000000000"

    def get_parameters_string(self):
        s = ''
        s = s + ("imei" + "=" + str(self.__imei))
        return s

    @property
    def imei(self):
        if self._rebuild: self._build()
        return self.__imei

    def get_dict(self):
        params_dict = {"imei": self.__imei}
        return params_dict

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketAnswerCommandGetImei, self)._parseBody()
        buffer = self.body
        self._number = unpack('<B', buffer[:1])[0]
        self.__imei = buffer.decode("ascii")[1:]


class PacketAnswerCommandGetRegisteredIButtons(PacketAnswer):
    """
     Answer on CommandGetRegisteredIButtons
    """
    _number = 5

    __numbers = [0]*5

    def get_parameters_string(self):
        s = ''
        for i in range(0, 5):
            s = s + ("number%d=%d; " % (i+1, self.__numbers[i]))
        return s

    @property
    def numbers(self):
        if self._rebuild: self._build()
        return self.__numbers

    def get_dict(self):
        params_dict = {"numbers": self.__numbers}
        return params_dict

    def _parseBody(self):
        super(PacketAnswerCommandGetRegisteredIButtons, self)._parseBody()
        buffer = self.body
        self._number = unpack('<B', buffer[:1])[0]
        #divide buffer into 5 chunks, 
        #add 2 zero bytes for unpacking and unpack as Q
        numbers = [unpack("<Q", buffer[6*i+1:6*(i+1)+1]+b'\x00\x00')[0] 
                   for i in range(0,5)]  
        self.__numbers = numbers


class PacketAnswerCommandGetPhones(PacketAnswer):
    """
     Answer on CommandGetPhones
    """
    _number = 7

    __phones = [0] * 5
    __call_sms_calls = [0] * 5
    __call_sms_smss = [0] * 5

    def get_parameters_string(self):
        s = ''
        for i in range(0, 5):
            s = s + ("phone%d=%s: incoming call %d incoming sms %d; " % 
                     (i+1, 
                      self.__phones[i], 
                      self.__call_sms_calls[i], 
                      self.__call_sms_smss[i]
                      )
            )
        return s


    @property
    def phones(self):
        if self._rebuild: self._build()
        return self.__phones

    @property
    def call_sms_calls(self):
        if self._rebuild: self._build()
        return self.__call_sms_calls

    @property
    def call_sms_smss(self):
        if self._rebuild: self._build()
        return self.__call_sms_smss

    def get_dict(self):
        params_dict = {"phones": self.phones, 
            "call_params": self.__call_sms_calls, 
            "sms_params": self.__call_sms_smss}
        return params_dict

    def _parseBody(self):
        super(PacketAnswerCommandGetPhones, self)._parseBody()
        buffer = self.body
        self._number = unpack('<B', buffer[:1])[0]

        for i in range(0, 5):
            self.__phones[i] = (buffer.decode("ascii")[i*11:(i+1)*11 - 1])
            call_sms = unpack("<B", buffer[(i+1)*11-1:(i+1)*11])[0]
            self.__call_sms_calls[i] = call_sms >> 4
            self.__call_sms_smss[i] = call_sms & 15

class PacketAnswerCommandGetTrackParams(PacketAnswer):
    """
     Answer on CommandGetTrackParams
    """
    _number = 10

    __filterCoordinates = 0
    __filterStraightPath = 0
    __filterRestructuring = 0
    __filterWriteOnEvent = 0
    __accelerometerSensitivity = 0
    __timeToStandby = 0
    __timeRecordingStandby = 0
    __timeRecordingMoving = 0
    __timeRecordingDistance = 0
    __drawingOnAngles = 0
    __minSpeed = 0
    __HDOP = 0
    __minspeed = 0
    __maxspeed = 0
    __acceleration = 0
    __jump = 0
    __idle = 0
    __courseDeviation = 0

    def get_parameters_string(self):
        s = ''
        s = s + ("fiter coordinates: %d; "\
                 "filter straight path: %d; "\
                 "filter restructuring: %d; "\
                 "filter (write on event): %d; "\
                 "accelerometer sensitivity: %d;"\
                 "time to standby: %d; "\
                 "standby recording time: %d; "\
                 "moving recording time: %d; "\
                 "distance recording time: %d; "\
                 "drawing on angles: %d; "\
                 "minSpeed: %d; "\
                 "HDOP: %d; "\
                 "minspeed: %d; "\
                 "maxspeed: %d; "\
                 "acceleration: %d; "\
                 "jump: %d; "\
                 "idle: %d; "\
                 "course deviation: %d; " % 
                 (self.__filterCoordinates,
                  self.__filterStraightPath,
                  self.__filterRestructuring,
                  self.__filterWriteOnEvent,
                  self.__accelerometerSensitivity,
                  self.__timeToStandby,
                  self.__timeRecordingStandby,
                  self.__timeRecordingMoving,
                  self.__timeRecordingDistance,
                  self.__drawingOnAngles,
                  self.__minSpeed,
                  self.__HDOP,
                  self.__minspeed,
                  self.__maxspeed,
                  self.__acceleration,
                  self.__jump,
                  self.__idle,
                  self.__courseDeviation,
                  )
        )

        return s

    def get_dict(self):
        params_dict = {"filter_coordinates": self.__filterCoordinates, 
                       "filter_straight_path": self.__filterStraightPath,
                       "filter_restructuring": self.__filterRestructuring,
                       "filter_write_on_event": self.__filterWriteOnEvent,
                       "accelerometer_sensitivity": 
                            self.__accelerometerSensitivity,
                       "time_to_standby": self.__timeToStandby,
                       "time_recording_standby": self.__timeRecordingStandby,
                       "time_recording_moving": self.__timeRecordingMoving,
                       "time_recording_distance": self.__timeRecordingDistance,
                       "drawing_on_angles": self.__drawingOnAngles,
                       "min_speed": self.__minSpeed,
                       "hdop": self.__HDOP,
                       "minspeed": self.__minspeed,
                       "maxspeed": self.__maxspeed,
                       "acceleration": self.__acceleration,
                       "jump": self.__jump,
                       "idle": self.__idle,
                       "course_deviation": self.__courseDeviation
        }
        return params_dict

    @property
    def filterCoordinates(self):
        if self._rebuild: self._build()
        return self.__filterCoordinates

    @property
    def filterStraightPath(self):
        if self._rebuild: self._build()
        return self.__filterStraightPath

    @property
    def filterRestructuring(self):
        if self._rebuild: self._build()
        return self.__filterRestructuring

    @property
    def filterWriteOnEvent(self):
        if self._rebuild: self._build()
        return self.__filterWriteOnEvent

    @property
    def accelerometerSensitivity(self):
        if self._rebuild: self._build()
        return self.__accelerometerSensitivity

    @property
    def timeToStandby(self):
        if self._rebuild: self._build()
        return self.__timeToStandby

    @property
    def timeRecordingStandby(self):
        if self._rebuild: self._build()
        return self.__timeRecordingStandby

    @property
    def timeRecordingMoving(self):
        if self._rebuild: self._build()
        return self.__timeRecordingMoving

    @property
    def timeRecordingDistance(self):
        if self._rebuild: self._build()
        return self.__timeRecordingDistance

    @property
    def drawingOnAngles(self):
        if self._rebuild: self._build()
        return self.__drawingOnAngles

    @property
    def minSpeed(self):
        if self._rebuild: self._build()
        return self.__minSpeed

    @property
    def HDOP(self):
        if self._rebuild: self._build()
        return self.__HDOP

    @property
    def minspeed(self):
        if self._rebuild: self._build()
        return self.__minspeed

    @property
    def maxspeed(self):
        if self._rebuild: self._build()
        return self.__maxspeed

    @property
    def acceleration(self):
        if self._rebuild: self._build()
        return self.__acceleration

    @property
    def jump(self):
        if self._rebuild: self._build()
        return self.__jump

    @property
    def idle(self):
        if self._rebuild: self._build()
        return self.__idle

    @property
    def courseDeviation(self):
        if self._rebuild: self._build()
        return self.__courseDeviation


    def _parseBody(self):
        super(PacketAnswerCommandGetTrackParams, self)._parseBody()
        buffer = self.body
        self._number = unpack('<B', buffer[:1])[0]
        _filter = unpack("<B", buffer[1:2])[0]

        self.__  = (_filter >> 7) & 1
        self.__filterStraightPath = (_filter >> 6) & 1
        self.__filterRestructuring = (_filter >> 5) & 1
        self.__filterWriteOnEvent = (_filter >> 4) & 1

        self.__accelerometerSensitivity = unpack("<H", buffer[2:4])[0]
        self.__timeToStandby = unpack("<H", buffer[4:6])[0]
        self.__timeRecordingStandby = unpack("<H", buffer[6:8])[0]
        self.__timeRecordingMoving = unpack("<H", buffer[8:10])[0]
        self.__timeRecordingDistance = unpack("<B", buffer[10:11])[0]
        self.__drawingOnAngles = unpack("<B", buffer[11:12])[0]
        self.__minSpeed = unpack("<B", buffer[12:13])[0]
        self.__HDOP = unpack("<B", buffer[13:14])[0]
        self.__minspeed = unpack("<B", buffer[14:15])[0]
        self.__maxspeed = unpack("<B", buffer[15:16])[0]
        self.__acceleration = unpack("<B", buffer[16:17])[0]
        self.__jump = unpack("<B", buffer[17:18])[0]
        self.__idle = unpack("<B", buffer[18:19])[0]
        self.__courseDeviation = unpack("<B", buffer[19:20])[0]

class PacketAnswerCommandSwitchSecurityMode(PacketAnswer):
    """
    Answer on CommandSwitchSecurityMode
    """
    _number = 200

    __serviceMessage200 = 0

    def get_parameters_string(self):
        s = ''
        s += ("service message 200: %d" % self.__serviceMessage200)
        return s

    @property
    def serviceMessage200(self):
        if self._rebuild: self._build()
        return self.__serviceMessage200

    def get_dict(self):
        params_dict = {"service_message_200": self.__serviceMessage200}
        return params_dict

    def get_parameters_string(self):
        s = ''
        s = s.join("service_message_200"+"="+str(self.__serviceMessage200))

    def _parseBody(self):
        super(PacketAnswerCommandSwitchSecurityMode, self)._parseBody()
        buffer = self.body
        self._number = unpack('<B', buffer[:1])[0]

        self.__serviceMessage200 = unpack('<H', buffer[1:3])[0]   

class PacketAnswerCommandGetImage(PacketAnswer):
    """
     Answer on CommandGetImage
    """
    _number = 20

    __code = 0
    __imageSize = 0
    __chunkNumber = 0
    __chunkData = None

    @property
    def code(self):
        if self._rebuild: self._build()
        return self.__code

    @property
    def imageSize(self):
        if self._rebuild: self._build()
        return self.__imageSize

    @property
    def chunkNumber(self):
        if self._rebuild: self._build()
        return self.__chunkNumber

    @property
    def chunkData(self):
        if self._rebuild: self._build()
        return self.__chunkData

    def get_dict(self):
        params_dict = {"code": self.__code, "image_size": self.__imageSize, 
            "chunk_number": self.__chunkNumber, "chunk_data":self.__chunkData}
        return params_dict

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketAnswerCommandGetImage, self)._parseBody()
        buffer = self._body
        self._number = unpack('<B', buffer[:1])[0]
        self.__code = unpack('<B', buffer[1:2])[0]
        if self.__code == IMAGE_ANSWER_CODE_SIZE:
            b, w = unpack('<HB', buffer[2:5])
            self.__imageSize = b | (w << 16)
        elif self.__code == IMAGE_ANSWER_CODE_DATA:
            self.__chunkNumber = unpack('<B', buffer[2:3])[0]
            chunkLength = unpack('<H', buffer[3:5])[0]
            self.__chunkData = buffer[5:5 + chunkLength]
            if len(self.__chunkData) != chunkLength:
                raise Exception('Incorrect image chunk length! ' +\
                    str(len(self.__chunkData)) + ' (given) != ' +\
                    str(chunkLength) + ' (must be)')

# ---------------------------------------------------------------------------
 

class PacketFactory(AbstractPacketFactory):
    """
     Packet factory
    """

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
        if not (number in classes):
            return None
        return classes[number]

    def getInstance(self, data = None):
        """
          Returns a tag instance by its number
        """
        if data == None: return

        # read header and length
        length = unpack("<H", data[:2])[0]
        number = length >> 14

        CLASS = self.getClass(number)
        if not CLASS:
            raise Exception('Packet %s is not found' % number)
        if issubclass(CLASS, PacketAnswer):
            CLASS = PacketAnswer.getInstance(data)
        if not CLASS:
            raise Exception('Class for %s is not found with number %s' 
                            % (data, number))
        return CLASS(data)

import inspect
import sys

def getAnswerClassByNumber(number):
    """
     Returns command answer's class by its number
     @param number: int Number of the command
     @return: Command class
    """
    for name, cls in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(cls) and \
            issubclass(cls, PacketAnswer) and\
                cls._number == number:
                    return cls
    return None

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
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9')
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(isinstance(packet, PacketData), False)
        self.assertEqual(packet.header, 0)
        self.assertEqual(packet.length, 18)
        self.assertEqual(packet.body, b'\x01\x00012896001609129\x06')
        self.assertEqual(packet.checksum, 47519)

    def test_setPacketBody(self):
        packet = self.factory.getInstance(
          b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9')
        self.assertEqual(packet.length, 18)
        self.assertEqual(isinstance(packet, PacketHead), True)
        self.assertEqual(packet.checksum, 47519)
        packet.body = b'\x22\x00012896001609129\x05'
        self.assertEqual(packet.length, 18)
        self.assertEqual(packet.deviceNumber, 34)
        self.assertEqual(packet.deviceImei, '012896001609129')
        self.assertEqual(packet.protocolVersion, 5)
        self.assertEqual(packet.rawData, 
            b'\x12\x00\x22\x00012896001609129\x05$6')
        self.assertEqual(packet.checksum, 13860)

    def test_packetTail(self):
        packets = self.factory.getPacketsFromBuffer(
            b'\x12\x00\x01\x00012896001609129\x06\x9f\xb9' +
            b'\x12\x00\x22\x00012896001609129\x05$6')
        self.assertEqual(len(packets), 2)
        p = packets[0]
        self.assertEqual(p.deviceImei, '012896001609129')

    def test_dataPacket(self):
        packets = self.factory.getPacketsFromBuffer(
            b'\xdcC\x01\x00\xff\xffh)\x8f\xf0\\Q\x10\xe0l,\x03\xe8\xbc' +
            b'\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\x98, \r%\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00i)\x08\xf1\\Q\x10' +
            b'\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08' +
            b'\x98,\x01\r$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80' +
            b'\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00j)\x81\xf1\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00' +
            b'\x00\x00\x00\xff\x08\x98,&\r$\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80' +
            b'\x80\x80\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00k)\xfa\xf1\\Q\x10\xe0l,\x03\xe8\xbc' +
            b'\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\xba,\xdc\x0c$\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00l)s\xf2\\Q\x10\xe0l,\x03' +
            b'\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\xba,\x01\r$' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00\x00\x00' +
            b'\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00m)\xec\xf2\\Q\x10\xe0l,' +
            b'\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff\x08\x98,' +
            b'\xf5\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00\x00' +
            b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00n)e\xf3\\Q\x10' +
            b'\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff(\xba,' +
            b'\xdc\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80\x00' +
            b'\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00o)\xde\xf3\\' +
            b'Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00\xff' +
            b'\x08\x98,\x0e\r%\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80\x80\x80' +
            b'\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00p)W\xf4' +
            b'\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00\x00\x00' +
            b'\xff\x08\x98,\xef\x0c$\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80\x80' +
            b'\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'q)\xd0\xf4\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\x08\x98,-\r$\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80' +
            b'\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00r)I\xf5\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00\x00' +
            b'\x00\x00\xff\x08\x98,\x0e\r%\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80\x80\x80' +
            b'\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00s)\xc2\xf5\\Q\x10\xe0l,\x03\xe8\xbc\xfd\x02\x00\x00\x00' +
            b'\x00\x00\x00\xff\x08\xba,\xef\x0c$\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x80' +
            b'\x80\x80\x80\x80\x80\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00' +
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            b'\x00\x00\x00=\xa9'
        )
        self.assertEqual(len(packets), 1)
        packet = packets[0]
        self.assertEqual(isinstance(packet, PacketData), True)
        self.assertEqual(len(packet.items), 12)
        packetItem = packet.items[3]
        self.assertEqual(isinstance(packetItem, PacketDataItem), True)
        self.assertEqual(packetItem.params['speed'], 0.0)
        self.assertEqual(packetItem.params['latitude'], 53.243104)
        self.assertEqual(packetItem.params['longitude'], 50.1834)
        self.assertEqual(packetItem.params['satellitescount'], 16)
        self.assertEqual(packetItem.params['time'].
            strftime('%Y-%m-%dT%H:%M:%S.%f'), '2013-04-04T03:22:34.000000')
        packetItem2 = packet.items[6]
        self.assertEqual(packetItem2.params['speed'], 0)
        self.assertEqual(packetItem2.params['satellitescount'], 16)
        self.assertEqual(packetItem2.number, 10606)
        self.assertEqual(packetItem2.params['sensors']['int_temperature'], 36)
        self.assertEqual(
            packetItem2.params['sensors']['ext_battery_voltage'], 11450)
        self.assertEqual(
            packetItem2.params['sensors']['sat_antenna_connected'], 1)

    def test_commandAnswerGetImage(self):
        data = b'\x05\x80\x14\x00\xb1\x46\x00\x03\x84'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertIsInstance(packet, PacketAnswerCommandGetImage)
        self.assertEqual(packet.command, 20)
        self.assertEqual(packet.code, 0)
        self.assertEqual(packet.imageSize, 18097)

    def test_commandAnswerGetImageChunk(self):
        data = b'\xff\x81\x14\x01\x00\xfa\x01\xff\xd8\xff\xdb\x00\x84' + \
               b'\x00\x13\r\x0e\x10\x0e\x0c\x13\x10\x0f\x10\x15\x14\x13' + \
               b'\x16\x1c/\x1e\x1c\x1a\x1a\x1c9)+"/D<GFC<B@KTl[KPfQ@B^\x80' + \
               b'_fosyzyIZ\x84\x8e\x83u\x8dlvyt\x01\x14\x15\x15\x1c\x19' +\
               b'\x1c7\x1e\x1e7tMBMtttttttttttttttttttttttttttttttttttt' +\
               b'tttttttttttttt\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03' +\
               b'\x01!\x00\x02\x11\x01\x03\x11\x01\xff\xdd\x00\x04\x00(' +\
               b'\xff\xc4\x01\xa2\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06' +\
               b'\x07\x08\t\n\x0b\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05' +\
               b'\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12' +\
               b'!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R' +\
               b'\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CD' +\
               b'EFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89' +\
               b'\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5' +\
               b'\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba' +\
               b'\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6' +\
               b'\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea' +\
               b'\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\x01\x00\x03\x01' +\
               b'\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00' +\
               b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x11\x00\x02\x01' +\
               b'\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01' +\
               b'\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B' +\
               b'\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17' +\
               b'\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvw\xc1\xb0'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet.chunkNumber, 0)
        self.assertEqual(len(packet.chunkData), 506)

    def test_commandPacketAnswerCommandGetImei(self):
        data = b'\x10\x80\x01868204003057949W!'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet._number, 1)
        self.assertEqual(packet.imei, '868204003057949')

    def test_commandPacketAnswerCommandGetRegisteredIButtons(self):
        data = b'\x1f\x80\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00i\xc6'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet._number, 5)
        self.assertEqual(len(packet.numbers), 5)
        self.assertEqual(packet.numbers[3], 0)

    def test_commandPacketAnswerCommandGetTrackParams(self):
        data = b'\x14\x80\n\x00 \x03<\x00\x14\x00\x1e'\
            b'\x00\x1e\x05\x03(\x03\x96\x1e2\x1e\x05O\xcc'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]

        self.assertEqual(packet._number, 10)
        self.assertEqual(packet.filterCoordinates, 0)
        self.assertEqual(packet.filterStraightPath, 0)
        self.assertEqual(packet.filterRestructuring, 0)
        self.assertEqual(packet.filterWriteOnEvent, 0)
        self.assertEqual(packet.accelerometerSensitivity, 800)
        self.assertEqual(packet.timeToStandby, 60)
        self.assertEqual(packet.timeRecordingStandby, 20)
        self.assertEqual(packet.timeRecordingMoving, 30)
        self.assertEqual(packet.timeRecordingDistance, 30)
        self.assertEqual(packet.drawingOnAngles, 5)
        self.assertEqual(packet.minSpeed, 3)
        self.assertEqual(packet.HDOP, 40)
        self.assertEqual(packet.minspeed, 3)
        self.assertEqual(packet.maxspeed, 150)
        self.assertEqual(packet.acceleration, 30)
        self.assertEqual(packet.jump, 50)
        self.assertEqual(packet.idle, 30)
        self.assertEqual(packet.courseDeviation, 5)

    def test_commandPacketAnswerCommandSwitchSecurityMode(self):
        data = b'\x03\x80\xc8\x00\x02I\xff'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet._number, 200)
        self.assertEqual(packet.serviceMessage200, 512)

    def test_commandError(self):
        data = b'\x02\x80\xfc\r\x80\xb1'
        packets = self.factory.getPacketsFromBuffer(data)


    def test_commandPacketAnswerCommandGetPhones(self):
        data = b'8\x80\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05E'
        packets = self.factory.getPacketsFromBuffer(data)
        packet = packets[0]
        self.assertEqual(packet._number, 7)
        self.assertEqual(packet.phones[3], '\x00\x00\x00\x00\x00'\
            '\x00\x00\x00\x00\x00')
        self.assertEqual(packet.call_sms_calls[4], 0)
        self.assertEqual(packet.call_sms_smss[2], 0)