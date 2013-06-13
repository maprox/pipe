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
    _command = 0

    @property
    def command(self):
        if self._rebuild: self._build()
        return self._command

    @classmethod
    def getInstance(cls, data = None):
        CLASS = None
        if data:
            command = unpack('<B', data[2:3])[0]
            CLASS = getAnswerClassByNumber(command)
        return CLASS

# ---------------------------------------------------------------------------

class Command(NavisetBase):
    """
     A command packet
    """

    # protected properties
    _fmtHeader = '<H'   # header format
    _fmtLength = None   # packet length format

    _header = 2
    _number = 0

    @property
    def number(self):
        if self._rebuild: self._build()
        return self._number

    def __init__(self, params = None):
        """
         Initialize command with specific params
         @param params: dict
         @return:
        """
        super(Command, self).__init__()
        self.setParams(params)

    def setParams(self, params):
        """
         Set command params if needed.
         Override in child classes.
         @param params: dict
         @return:
        """
        self._rebuild = True

    def _parseHeader(self):
        # read header and command number
        unpacked = unpack('<BB', self._head)
        self._header = unpacked[0]
        self._number = unpacked[1]
        headerCode = 0x02
        if (self._header != headerCode):
            raise Exception('Incorrect command packet! ' +\
                            str(self._header) + ' (given) != ' +\
                            str(headerCode) + ' (must be)')

    def _buildHead(self):
        data = b''
        data += pack('<B', self._header)
        data += pack('<B', self._number)
        return data

# ---------------------------------------------------------------------------
# Simple commands
# ---------------------------------------------------------------------------

class CommandGetStatus(Command): _number = 0
class CommandGetImei(Command): _number = 1
class CommandGetRegisteredIButtons(Command): _number = 5
class CommandGetPhones(Command): _number = 7
class CommandGetTrackParams(Command): _number = 10
class CommandRemoveTrackFromBuffer(Command): _number = 16
class CommandRestart(Command): _number = 18

# ---------------------------------------------------------------------------

class CommandChangeDeviceNumber(Command):
    """
     Change device number
    """
    _number = 2

    # private params
    __deviceNumber = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.deviceNumber = params['deviceNumber'] or 0

    @property
    def deviceNumber(self):
        if self._rebuild: self._build()
        return self.__deviceNumber

    @deviceNumber.setter
    def deviceNumber(self, value):
        if 0 <= value <= 0xFFFF:
            self.__deviceNumber = value
            self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<H', self.__deviceNumber)
        return data

class CommandChangeDevicePassword(Command):
    """
    Change device password
    """
    _number = 3
    
    # private params
    __devicePassword = 0
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.devicePassword = params['devicePassword'] or 0
    
    @property
    def devicePassword(self):
        pass
        if self._rebuild: self._build()
        return self.__devicePassword
    
    @devicePassword.setter
    def devicePassword(self, value):
        if 0 <= value <= 0xFFFF:
            self.__devicePassword = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        data += pack('<H', self.__devicePassword)
        return data

class CommandSetGprsParams(Command):
    """
     Change device GPRS params
    """
    _number = 4

    # private params
    __ip = ''
    __port = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.ip = params['ip'] or ''
        self.port = params['port'] or 0

    @property
    def ip(self):
        if self._rebuild: self._build()
        return self.__ip

    @ip.setter
    def ip(self, value):
        self.__ip = str(value)
        self._rebuild = True

    @property
    def port(self):
        if self._rebuild: self._build()
        return self.__port

    @port.setter
    def port(self, value):
        if (0 <= value <= 0xFFFF):
            self.__port = value
            self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += socket.inet_aton(self.__ip)
        data += pack('<H', self.__port)
        return data

PROCESS_KEY_NUMBER_ACTION_ADD = 0
PROCESS_KEY_NUMBER_ACTION_REMOVE = 1

class CommandAddRemoveKeyNumber(Command):
    """
    Adds or removes device key for selected cell.
    """
    _number = 6
    
    # private params
    __processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_ADD
    __processCellNumber = 0
    __keyNumber = 0
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.processKeyNumberAction = params['processKeyNumberAction']
        self.processCellNumber = params['processCellNumber']
        self.keyNumber = params['keyNumber']
    
    @property
    def processKeyNumberAction(self):
        if self._rebuild: self._build()
        return self.__processKeyNumberAction
    
    @processKeyNumberAction.setter
    def processKeyNumberAction(self, value):
        if 0 <= value <= 1:
            self.__processKeyNumberAction = value
            self._rebuild = True
    
    @property
    def processCellNumber(self):
        if self._rebuild: self._build()
        return self.__processCellNumber
    
    @processCellNumber.setter
    def processCellNumber(self, value):
        if 0 <= value <= 15:
            self.__processCellNumber = value
            self._rebuild = True
    
    @property
    def keyNumber(self):
        if self._rebuild: self._build()
        return self.__keyNumber
    
    @keyNumber.setter
    def keyNumber(self, value):
        if 0 <= value <= 256**6 - 1:
            self.__keyNumber = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        processPacked = 16 * self.processKeyNumberAction + self.processCellNumber
        data += pack('<B', processPacked)
        data += pack('<Q', self.__keyNumber)[:-2]
        return data

CALL_SMS_CALL_RECEIVE = 0
CALL_SMS_CALL_SWITCH_TO_VOICE_MENU = 1
CALL_SMS_CALL_CHANGE_SECURITY = 2
CALL_SMS_CALL_STOP = 3

CALL_SMS_SMS_IGNORE = 0
CALL_SMS_SMS_RECEIVE = 1

class CommandAddRemovePhoneNumber(Command):
    """
    Add or remove phone number and change its parameters
    """
    _number = 8
    
    #private params
    __processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_ADD
    __processCellNumber = 0
    __phoneNumber = "0000000000"
    __callSmsCall = CALL_SMS_CALL_RECEIVE 
    __callSmsSms = CALL_SMS_SMS_IGNORE
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.processKeyNumberAction = params['processKeyNumberAction'] or PROCESS_KEY_NUMBER_ACTION_ADD
        self.processCellNumber = params['processCellNumber'] or 0
        self.phoneNumber = params['phoneNumber'] or "0000000000"
        self.callSmsCall = params['callSmsCall'] or CALL_SMS_CALL_RECEIVE 
        self.callSmsSms = params['callSmsSms'] or CALL_SMS_CALL_IGNORE
    
    @property
    def processKeyNumberAction(self):
        if self._rebuild: self._build()
        return self.__processKeyNumberAction
    
    @processKeyNumberAction.setter
    def processKeyNumberAction(self, value):
        if 0 <= value <= 0x1:
            self.__processKeyNumberAction = value
            self._rebuild = True
    
    @property
    def processCellNumber(self):
        if self._rebuild: self._build()
        return self.__processCellNumber
    
    @processCellNumber.setter
    def processCellNumber(self, value):
        if 0 <= value <= 15:
            self.__processCellNumber = value
            self._rebuild = True
    
    @property
    def phoneNumber(self):
        if self._rebuild: self._build()
        return self.__phoneNumber
    
    @phoneNumber.setter
    def phoneNumber(self, value):
        self.__phoneNumber = str(value)
        self._rebuild = True
    
    @property
    def callSmsCall(self):
        if self._rebuild: self._build()
        return self.__callSmsCall
    
    @callSmsCall.setter
    def callSmsCall(self, value):
        if 0 <= value <= 15:
            self.__callSmsCall = value
            self._rebuild = True
    
    @property
    def callSmsSms(self):
        if self._rebuild: self._build()
        return self.__callSmsSms
    
    @callSmsSms.setter
    def callSmsSms(self, value):
        if 0 <= value <= 15:
            self.__callSmsSms = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        processPacked = 16 * self.processKeyNumberAction + self.processCellNumber
        data += pack('<B', processPacked)
        phoneNumberBytes = bytes(self.phoneNumber, "ascii")
        data += pack('<s', phoneNumberBytes)
        callSmsPacked = 16 * self.callSmsCall + self.callSmsSms
        data += pack('<B', callSmsPacked)
        return data       
    
    


class CommandProtocolTypeStructure(Command):
    """
    Sets protocol type and structure 
    """
    _number = 9
    
    #private params
    __protocolType = 0
    __protocolStructure = 0
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.protocolType = params['protocolType'] or 0
        self.protocolStructure = params['protocolStructure'] or 0
    
    @property
    def protocolType(self):
        if self._rebuild: self._build()
        return self.__protocolType
    
    @protocolType.setter
    def protocolType(self, value):
        if 0 <= value <= 0xFF:
            self.__protocolType = value
            self._rebuild = True
    
    @property
    def protocolStructure(self):
        if self._rebuild: self._build()
        return self.__protocolStructure
    
    @protocolStructure.setter
    def protocolStructure(self, value):
        if 0 <= value <= 0xFFFFFFFF:
            self.__protocolStructure = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        data += pack('<B', self.__protocolType)
        data += pack('<Q', self.__protocolStructure)
        return data    
    

class CommandFiltrationDrawingParameters(Command):
    """
    Sets filtration and drawing
    """
    _number = 11
    #private params
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
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.filterCoordinates = params['filterCoordinates'] or 0
        self.filterStraightPath = params['filterStraightPath'] or 0
        self.filterRestructuring = params['filterRestructuring'] or 0
        self.filterWriteOnEvent = params['filterWriteOnEvent'] or 0
        self.accelerometerSensitivity = params['accelerometerSensitivity'] or 0
        self.timeToStandby = params['timeToStandby'] or 0
        self.timeRecordingStandby = params['timeRecordingStandby'] or 0
        self.timeRecordingMoving = params['timeRecordingMoving'] or 0
        self.timeRecordingDistance = params['timeRecordingDistance'] or 0
        self.drawingOnAngles = params['drawingOnAngles'] or 0
        self.minSpeed = params['minSpeed'] or 0
        self.HDOP = params['HDOP'] or 0
        self.minspeed = params['minspeed'] or 0
        self.maxspeed = params['maxspeed'] or 0
        self.acceleration = params['acceleration'] or 0
        self.jump = params['jump'] or 0
        self.idle = params['idle'] or 0
        self.courseDeviation = params['courseDeviation'] or 0
    
    @property
    def filterCoordinates(self):
        if self._rebuild: self._build()
        return self.__filterCoordinates
    
    @filterCoordinates.setter
    def filterCoordinates(self, value):
        if 0 <= value <= 1:
            self.__filterCoordinates = value
            self._rebuild = True

    @property
    def filterStraightPath(self):
        if self._rebuild: self._build()
        return self.__filterStraightPath
    
    @filterStraightPath.setter
    def filterStraightPath(self, value):
        if 0 <= value <= 1:
            self.__filterStraightPath = value
            self._rebuild = True
            
    @property
    def filterRestructuring(self):
        if self._rebuild: self._build()
        return self.__filterRestructuring
    
    @filterRestructuring.setter
    def filterRestructuring(self, value):
        if 0 <= value <= 1:
            self.__filterRestructuring = value
            self._rebuild = True

    @property
    def filterWriteOnEvent(self):
        if self._rebuild: self._build()
        return self.__filterWriteOnEvent
    
    @filterWriteOnEvent.setter
    def filterWriteOnEvent(self, value):
        if 0 <= value <= 1:
            self.__filterWriteOnEvent = value
            self._rebuild = True
    
    @property
    def accelerometerSensitivity(self):
        if self._rebuild: self._build()
        return self.__accelerometerSensitivity
    
    @accelerometerSensitivity.setter
    def accelerometerSensitivity(self, value):
        if 0 <= value <= 0xFFFF:
            self.__accelerometerSensitivity = value
            self._rebuild = True

    @property
    def timeToStandby(self):
        if self._rebuild: self._build()
        return self.__timeToStandby
    
    @timeToStandby.setter
    def timeToStandby(self, value):
        if 0 <= value <= 0xFFFF:
            self.__timeToStandby = value
            self._rebuild = True

    @property
    def timeRecordingStandby(self):
        if self._rebuild: self._build()
        return self.__timeRecordingStandby
    
    @timeRecordingStandby.setter
    def timeRecordingStandby(self, value):
        if 0 <= value <= 0xFFFF:
            self.__timeRecordingStandby = value
            self._rebuild = True    

    @property
    def timeRecordingMoving(self):
        if self._rebuild: self._build()
        return self.__timeRecordingMoving
    
    @timeRecordingMoving.setter
    def timeRecordingMoving(self, value):
        if 0 <= value <= 0xFFFF:
            self.__timeRecordingMoving = value
            self._rebuild = True    

    @property
    def timeRecordingDistance(self):
        if self._rebuild: self._build()
        return self.__timeRecordingDistance
    
    @timeRecordingDistance.setter
    def timeRecordingDistance(self, value):
        if 0 <= value <= 0xFF:
            self.__timeRecordingDistance = value
            self._rebuild = True

    @property
    def drawingOnAngles(self):
        if self._rebuild: self._build()
        return self.__drawingOnAngles
    
    @drawingOnAngles.setter
    def drawingOnAngles(self, value):
        if 0 <= value <= 0xFF:
            self.__drawingOnAngles = value
            self._rebuild = True    

    @property
    def minSpeed(self):
        if self._rebuild: self._build()
        return self.__minSpeed
    
    @minSpeed.setter
    def minSpeed(self, value):
        if 0 <= value <= 0xFF:
            self.__minSpeed = value
            self._rebuild = True

    @property
    def HDOP(self):
        if self._rebuild: self._build()
        return self.__HDOP
    
    @HDOP.setter
    def HDOP(self, value):
        if 0 <= value <= 0xFF:
            self.__HDOP = value
            self._rebuild = True

    @property
    def minspeed(self):
        if self._rebuild: self._build()
        return self.__minspeed
    
    @minspeed.setter
    def minspeed(self, value):
        if 0 <= value <= 0xFF:
            self.__minspeed = value
            self._rebuild = True

    @property
    def maxspeed(self):
        if self._rebuild: self._build()
        return self.__maxspeed
    
    @maxspeed.setter
    def maxspeed(self, value):
        if 0 <= value <= 0xFF:
            self.__maxspeed = value
            self._rebuild = True
    @property
    def acceleration(self):
        if self._rebuild: self._build()
        return self.__acceleration
    
    @acceleration.setter
    def acceleration(self, value):
        if 0 <= value <= 0xFF:
            self.__acceleration = value
            self._rebuild = True
    @property
    def idle(self):
        if self._rebuild: self._build()
        return self.__idle
    
    @idle.setter
    def idle(self, value):
        if 0 <= value <= 0xFF:
            self.__idle = value
            self._rebuild = True

    @property
    def jump(self):
        if self._rebuild: self._build()
        return self.__jump
    
    @jump.setter
    def jump(self, value):
        if 0 <= value <= 0xFF:
            self.__jump = value
            self._rebuild = True

    @property
    def courseDeviation(self):
        if self._rebuild: self._build()
        return self.__courseDeviation
    
    @courseDeviation.setter
    def courseDeviation(self, value):
        if 0 <= value <= 0xFF:
            self.__courseDeviation = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        filterPacked = 128 * self.__filterCoordinates + 64 * self.__filterStraightPath + 32 * self.__filterRestructuring + 16 * self.__filterWriteOnEvent
        data += pack('<B', filterPacked)
        data += pack('<H', self.__accelerometerSensitivity)
        data += pack('<H', self.__timeToStandby)
        data += pack('<H', self.__timeRecordingStandby)
        data += pack('<H', self.__timeRecordingMoving)
        data += pack('<B', self.__timeRecordingDistance)
        data += pack('<B', self.__drawingOnAngles)
        data += pack('<B', self.__minSpeed)
        data += pack('<B', self.__HDOP)
        data += pack('<B', self.__minspeed)
        data += pack('<B', self.__maxspeed)
        data += pack('<B', self.__acceleration)
        data += pack('<B', self.__idle)
        data += pack('<B', self.__jump)
        data += pack('<B', self.__courseDeviation)
        return data    


ACTIVE_LEVEL_LOW_OR_HIGH = 0
ACTIVE_LEVEL_LOW = 1
ACTIVE_LEVEL_FREE = 2
ACTIVE_LEVEL_HIGH = 3
ACTIVE_LEVEL_LOW_WITH_HYSTERESIS = 4
ACTIVE_LEVEL_HIGH_WITH_HYSTERESIS = 5

class CommandConfigureInputs(Command):
    """
    Configures device inputs.
    """
    
    _number = 12
    
    # private params
    __inputActActiveLevel = ACTIVE_LEVEL_LOW_OR_HIGH
    __inputActInputNumber = 0
    __lowerBorder = 0
    __upperBorder = 0
    __filterLength = 0
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.inputActActiveLevel = params['inputActActiveLevel']
        self.inputActInputNumber = params['inputActInputNumber']
        self.lowerBorder = params['lowerBorder']
        self.upperBorder = params['upperBorder']
        self.filterLength = params['filterLength']
    
    @property
    def inputActActiveLevel(self):
        if self._rebuild: self._build()
        return self.__inputActActiveLevel
    
    @inputActActiveLevel.setter
    def inputActActiveLevel(self, value):
        if 0 <= value <= 5:
            self.__inputActActiveLevel = value
            self._rebuild = True
    
    @property
    def inputActInputNumber(self):
        if self._rebuild: self._build()
        return self.__inputActInputNumber
    
    @inputActInputNumber.setter
    def inputActInputNumber(self, value):
        if 0 <= value <= 0xF:
            self.__inputActInputNumber = value
            self._rebuild = True
    
    @property
    def lowerBorder(self):
        if self._rebuild: self._build()
        return self.__lowerBorder
    
    @lowerBorder.setter
    def lowerBorder(self, value):
        if 0 <= value <= 0xFFFF:
            self.__lowerBorder = value
            self._rebuild = True
    
    @property
    def upperBorder(self):
        if self._rebuild: self._build()
        return self.__upperBorder
    
    @upperBorder.setter
    def upperBorder(self, value):
        if 0 <= value <= 0xFFFF:
            self.__upperBorder = value
            self._rebuild = True
    
    @property
    def filterLength(self):
        if self._rebuild: self._build()
        return self.__filterLength
    
    @filterLength.setter
    def filterLength(self, value):
        if 0 <= value <= 0xFF:
            self.__filterLength = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        inputActPacked = 16 * self.__inputActActiveLevel + self.__inputActInputNumber 
        data += pack('<B', inputActPacked)
        data += pack('<H', self.__lowerBorder)
        data += pack('<H', self.__upperBorder)
        data += pack('<B', self.__filterLength)
        return data    

OUTPUT_TURN_OFF = 0
OUTPUT_TURN_ON = 1
OUTPUT_IMPULSE = 2

class CommandConfigureOutputs(Command):
    """
    Configures device outputs.
    """
    
    _number = 13
    
    # private params
    __outputMode = OUTPUT_TURN_OFF
    __outputExitNumber = 0
    __impulseLength = 0
    __pauseLength = 0
    __repeatNumber = 0
    
    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.outputMode = params['outputMode']
        self.outputExitNumber = params['outputExitNumber']
        self.impulseLength = params['impulseLength']
        self.pauseLength = params['pauseLength']
        self.repeatNumber = params['repeatNumber']
    
    @property
    def outputMode(self):
        if self._rebuild: self._build()
        return self.__outputMode
    
    @outputMode.setter
    def outputMode(self, value):
        if 0 <= value <= 2:
            self.__outputMode = value
            self._rebuild = True
    
    @property
    def outputExitNumber(self):
        if self._rebuild: self._build()
        return self.__outputExitNumber
    
    @outputExitNumber.setter
    def outputExitNumber(self, value):
        if 0 <= value <= 0xF:
            self.__outputExitNumber = value
            self._rebuild = True
    
    @property
    def impulseLength(self):
        if self._rebuild: self._build()
        return self.__impulseLength
    
    @impulseLength.setter
    def impulseLength(self, value):
        if 0 <= value <= 0xFF:
            self.__impulseLength = value
            self._rebuild = True
    
    @property
    def pauseLength(self):
        if self._rebuild: self._build()
        return self.__pauseLength
    
    @pauseLength.setter
    def pauseLength(self, value):
        if 0 <= value <= 0xFF:
            self.__pauseLength = value
            self._rebuild = True
    
    @property
    def repeatNumber(self):
        if self._rebuild: self._build()
        return self.__repeatNumber
    
    @repeatNumber.setter
    def repeatNumber(self, value):
        if 0 <= value <= 0xFF:
            self.__repeatNumber = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        outputPacked = 16 * self.__outputMode + self.__outputExitNumber 
        data += pack('<B', outputPacked)
        data += pack('<B', self.__impulseLength)
        data += pack('<B', self.__pauseLength)
        data += pack('<B', self.__repeatNumber)
        return data    
    

SECURITY_MODE_IS_OFF = 0
SECURITY_MODE_IS_ON = 1

class CommandSwitchSecurityMode(Command):
    """
     Command for switching security number
    """
    _number = 14

    # private params
    __securityMode = SECURITY_MODE_IS_OFF

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.securityMode = params['securityMode'] or 0

    @property
    def securityMode(self):
        if self._rebuild: self._build()
        return self.__securityMode

    @securityMode.setter
    def securityMode(self, value):
        if 0 <= value <= 1:
            self.__securityMode = str(value)
            self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__securityMode))
        return data 

class CommandTemporarySecurityParameters(Command):
    """
     Command for setting temporary security parameters
    """
    _number = 15
    
    # private params
    __enterTime = 0
    __exitTime = 0
    __memoryTime = 0
    
    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.enterTime = params['enterTime'] or 0
        self.exitTime = params['exitTime'] or 0
        self.memoryTime = params['memoryTime'] or 0
    
    @property
    def enterTime(self):
        if self._rebuild: self._build()
        return self.__enterTime
    
    @enterTime.setter
    def enterTime(self, value):
        if 0 <= value <= 0xFF:
            self.__enterTime = value
            self._rebuild = True
    
    @property
    def exitTime(self):
        if self._rebuild: self._build()
        return self.__exitTime
    
    @exitTime.setter
    def exitTime(self, value):
        if 0 <= value <= 0xFF:
            self.__exitTime = value
            self._rebuild = True
    
    @property
    def memoryTime(self):
        if self._rebuild: self._build()
        return self.__memoryTime
    
    @memoryTime.setter
    def memoryTime(self, value):
        if 0 <= value <= 0xFF:
            self.__memoryTime = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        data += pack('<B', self.__enterTime)
        data += pack('<B', self.__exitTime)
        data += pack('<B', self.__memoryTime)
        return data

class CommandVoiceConnectionParameters(Command):
    """
     Command for setting voice connection parameters 
    """
    _number = 17
    
    # private params
    __microphoneGain = 0
    __speakerGain = 0
    __autodialDialNumber = 0
    __voiceMenuVolume = 0
    
    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.microphoneGain = params['microphoneGain'] or 0
        self.speakerGain = params['speakerGain'] or 0
        self.autodialDialNumber = params['autodialDialNumber'] or 0
        self.voiceMenuVolume = params['voiceMenuVolume'] or 0
    
    @property
    def microphoneGain(self):
        if self._rebuild: self._build()
        return self.__microphoneGain
    
    @microphoneGain.setter
    def microphoneGain(self, value):
        if 0 <= value <= 0xFF:
            self.__microphoneGain = value
            self._rebuild = True
    
    @property
    def speakerGain(self):
        if self._rebuild: self._build()
        return self.__speakerGain
    
    @speakerGain.setter
    def speakerGain(self, value):
        if 0 <= value <= 0xFF:
            self.__speakerGain = value
            self._rebuild = True
    
    @property
    def autodialDialNumber(self):
        if self._rebuild: self._build()
        return self.__autodialDialNumber
    
    @autodialDialNumber.setter
    def autodialDialNumber(self, value):
        if 0 <= value <= 0xFF:
            self.__autodialDialNumber = value
            self._rebuild = True

    @property
    def voiceMenuVolume(self):
        if self._rebuild: self._build()
        return self.__voiceMenuVolume
    
    @voiceMenuVolume.setter
    def voiceMenuVolume(self, value):
        if 0 <= value <= 0xFF:
            self.__voiceMenuVolume = value
            self._rebuild = True
    
    def _buildBody(self):
        """
        Builds body of the packet
        @return: body binstring
        """
        data = b''
        data += pack('<B', self.__microphoneGain)
        data += pack('<B', self.__speakerGain)
        data += pack('<B', self.__autodialDialNumber)
        data += pack('<B', self.__voiceMenuVolume)
        return data
        

# ---------------------------------------------------------------------------


class CommandSoftwareUpgrade(Command):
    """
     Change device GPRS params
    """
    _number = 19

    # private params
    __ip = ''
    __port = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.ip = params['ip'] or ''
        self.port = params['port'] or 0
    
    @property
    def ip(self):
        if self._rebuild: self._build()
        return self.__ip

    @ip.setter
    def ip(self, value):
        self.__ip = str(value)
        self._rebuild = True

    @property
    def port(self):
        if self._rebuild: self._build()
        return self.__port

    @port.setter
    def port(self, value):
        if (0 <= value <= 0xFFFF):
            self.__port = value
            self._rebuild = True
    
    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += socket.inet_aton(self.__ip)
        data += pack('<H', self.__port)
        return data

IMAGE_RESOLUTION_80x64 = 0
IMAGE_RESOLUTION_160x128 = 1
IMAGE_RESOLUTION_320x240 = 2
IMAGE_RESOLUTION_640x480 = 3
IMAGE_PACKET_CONFIRM_OK = 16
IMAGE_PACKET_CONFIRM_CORRUPT = 32

class CommandGetImage(Command):
    """
     Command for image receiving/confirmation
    """
    _number = 20

    # private params
    __type = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.type = params['type'] or 0

    @property
    def type(self):
        if self._rebuild: self._build()
        return self.__type

    @type.setter
    def type(self, value):
        self.__type = str(value)
        self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__type))
        return data

class CommandGetConfiguration(Command):
    """
     Command for receiving configuration
    """
    _number = 21

    # private params
    __configurationNumber = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.configurationNumber = params['configurationNumber'] or 0

    @property
    def configurationNumber(self):
        if self._rebuild: self._build()
        return self.__configurationNumber

    @configurationNumber.setter
    def configurationNumber(self, value):
        self.__configurationNumber = value
        self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__configurationNumber))
        return data

class CommandWriteConfiguration(Command):
    """
     Command for writing configuration
    """
    _number = 22
    
    #private params
    __configurationNumber = 0
    __configurationSize = 0
    __configurationData = ""
    
    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.configurationNumber = params['configurationNumber'] or 0
        self.configurationSize = params['configurationSize'] or 0
        self.configurationData = params['configurationData'] or 0
    
    @property
    def configurationNumber(self):
        if self._rebuild: self._build()
        return self.__configurationNumber

    @configurationNumber.setter
    def configurationNumber(self, value):
        if (0 <= value <= 0xFF):
            self.__configurationNumber = value
            self._rebuild = True
    
    @property
    def configurationSize(self):
        if self._rebuild: self._build()
        return self.__configurationSize

    @configurationSize.setter
    def  configurationSize(self, value):
        if (0 <= value <= 512):
            self.__configurationSize = value
            self._rebuild = True
    
    @property
    def configurationSize(self):
        if self._rebuild: self._build()
        return self.__configurationSize

    @configurationSize.setter
    def  configurationSize(self, value):
        self.__configurationSize = value
        self._rebuild = True
    
    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__configurationNumber))
        data += pack('<B', int(self.__configurationSize))
        configurationDataBytes = bytes(self.__configurationData, "ascii")
        data += pack('<s', configurationDataBytes)
        
        return data


class CommandSwitchToNewSim(Command):
    """
     Command for switching to new SIM number
    """
    _number = 23

    # private params
    __simNumber = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.simNumber = params['simNumber'] or 0

    @property
    def simNumber(self):
        if self._rebuild: self._build()
        return self.__simNumber

    @simNumber.setter
    def simNumber(self, value):
        self.__simNumber = str(value)
        self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__simNumber))
        return data


class CommandSwitchToConfigurationServer(Command):
    """
     Change device GPRS params
    """
    _number = 24

    # private params
    __ip = ''
    __port = 0

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.ip = params['ip'] or ''
        self.port = params['port'] or 0
    
    @property
    def ip(self):
        if self._rebuild: self._build()
        return self.__ip

    @ip.setter
    def ip(self, value):
        self.__ip = str(value)
        self._rebuild = True

    @property
    def port(self):
        if self._rebuild: self._build()
        return self.__port

    @port.setter
    def port(self, value):
        if (0 <= value <= 0xFFFF):
            self.__port = value
            self._rebuild = True
    
    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += socket.inet_aton(self.__ip)
        data += pack('<H', self.__port)
        return data
    
# ---------------------------------------------------------------------------
 

SIM_AUTOSWITCHING_IS_DISALLOWED = 0
SIM_AUTOSWITCHING_IS_ALLOWED = 1

class CommandAllowDisallowSimAutoswitching(Command):
    """
     Command for switching to new SIM number
    """
    _number = 25

    # private params
    __simAutoswitchingIsAllowed = SIM_AUTOSWITCHING_IS_DISALLOWED

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.simAutoswitchingIsAllowed = params['simAutoswitchingIsAllowed'] or 0

    @property
    def simAutoswitchingIsAllowed(self):
        if self._rebuild: self._build()
        return self.__simAutoswitchingIsAllowed

    @simAutoswitchingIsAllowed.setter
    def simAutoswitchingIsAllowed(self, value):
        if 0 <= value <= 1:
            self.__simAutoswitchingIsAllowed = str(value)
            self._rebuild = True

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        data = b''
        data += pack('<B', int(self.__simAutoswitchingIsAllowed))
        return data

# ---------------------------------------------------------------------------

IMAGE_ANSWER_CODE_SIZE = 0
IMAGE_ANSWER_CODE_DATA = 1
IMAGE_ANSWER_CODE_CAMERA_NOT_FOUND = 2
IMAGE_ANSWER_CODE_CAMERA_IS_BUSY = 3

class PacketAnswerCommandChangeDeviceNumber(PacketAnswer): _number = 2
class PacketAnswerCommandChangeDevicePassword(PacketAnswer): _number = 3
class PacketAnswerCommandSetGprsParams(PacketAnswer): _number = 4
class PacketAnswerCommandAddRemoveKeyNumber(PacketAnswer): _number = 6
class PacketAnswerCommandAddRemovePhoneNumber(PacketAnswer): _number = 8
class PacketAnswerCommandProtocolTypeStructure(PacketAnswer): _number = 9
class PacketAnswerCommandFiltrationDrawingParameters(PacketAnswer): _number = 11
class PacketAnswerCommandConfigureInputs(PacketAnswer): _number = 12
class PacketAnswerCommandConfigureOutputs(PacketAnswer): _number = 13
class PacketAnswerCommandTemporarySecurityParameters(PacketAnswer): _number = 15
class PacketAnswerCommandRemoveTrackFromBuffer(PacketAnswer): _number = 16
class PacketAnswerCommandVoiceConnectionParameters(PacketAnswer): _number = 17
class PacketAnswerCommandRestart(PacketAnswer): _number = 18
class PacketAnswerCommandSoftwareUpgrade(PacketAnswer): _number = 19
class PacketAnswerCommandSwitchToNewSim(PacketAnswer): _number = 23
class PacketAnswerCommandSwitchToConfigurationServer(PacketAnswer): _number = 24
class PacketAnswerCommandAllowDisallowSimAutoswitching(PacketAnswer): _number = 25


class PacketAnswerCommandGetImage(PacketAnswer):
    """
     Answer on CommandGetImage
    """
    _command = 20

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

    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        super(PacketAnswerCommandGetImage, self)._parseBody()
        buffer = self._body
        self._command = unpack('<B', buffer[:1])[0]
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

class PacketAnswerCommandGetImei(PacketAnswer):
    """
     Answer on CommandGetImei
    """
    _command = 1
    
    __imei = "000000000000000"
    
    @property
    def imei(self):
        if self._rebuild: self._build()
        return self.__imei
    
    def _parseBody(self):
        """
         Parses body of the packet
         @param body: Body bytes
         @protected
        """
        print("Got Imei!")
        super(PacketAnswerCommandGetImei, self)._parseBody()
        buffer = self.body        
        self._command = unpack('<B', buffer[:1])[0]
        self.__imei = buffer.decode("ascii")[1:]
        print("Imei is %s" % self.__imei)

class PacketAnswerCommandGetPhones(PacketAnswer):
    """
     Answer on CommandGetPhones
    """
    _command = 7
    
    __phones = [0]*5
    __call_sms_calls = [0] * 5
    __call_sms_smss = [0] * 5
    
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
    
    def _parseBody(self):
        print("Got phones!")
        super(PacketAnswerCommandGetPhones, self)._parseBody()
        buffer = self.body
        self._command = unpack('<B', buffer[:1])[0]
        
        
        for i in range(0, 5):
            self.__phones[i] = buffer.decode("ascii")[i*11:(i+1)*11 - 1]
            call_sms = unpack("<B", buffer[(i+1)*11-1:(i+1)*11])[0]
            self.__call_sms_calls[i] = call_sms >> 4
            self.__call_sms_smss[i] = call_sms & 15
        
        
        print(buffer)



class PacketAnswerCommandGetRegisteredIButtons(PacketAnswer):
    """
     Answer on CommandGetRegisteredIButtons
    """
    _command = 5
    
    __numbers = [0]*5
    
    @property
    def numbers(self):
        if self._rebuild: self._build()
        return self.__numbers
    
    def _parseBody(self):
        print("Got IButtons!")
        
        super(PacketAnswerCommandGetRegisteredIButtons, self)._parseBody()
        buffer = self.body
        print(buffer)
        self._command = unpack('<B', buffer[:1])[0]
        
        print(self._command)
        
        numbers = [unpack("<Q", buffer[6*i+1:6*(i+1)+1]+b'\x00\x00') for i in range(0,5)]  #divide buffer into 5 chunks, add 2 zero bytes for unpacking and unpack as Q
        self.__numbers = numbers
        

class PacketAnswerCommandGetTrackParams(PacketAnswer):
    """
     Answer on CommandGetTrackParams
    """
    _command = 10
    
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
        print("Got tracker parameters")
        buffer = self.body
        _filter = unpack("<B", buffer[0:1])[0]
        print("Filter:")
        print(_filter)
        print(_filter >> 7)
        print((_filter >> 7) & 1)
        self.__filterCoordinates = (_filter >> 7) & 1
        self.__filterStraightPath = (_filter >> 6) & 1
        self.__filterRestructuring = (_filter >> 5) & 1
        self.__filterWriteOnEvent = (_filter >> 4) & 1
        
        #print(self.__filterCoordinates)
        #print(self.__filterStraightPath)
        #print(self.__filterRestructuring)
        #print(self.__filterWriteOnEvent)
        
        self.__accelerometerSensitivity = unpack("<B", buffer[1:2])
        self.__timeToStandby = unpack("<H", buffer[2:4])
        self.__timeRecordingStandby = unpack("<H", buffer[4:6])
        self.__timeRecordingMoving = unpack("<H", buffer[6:8])
        self.__timeRecordingDistance = unpack("<H", buffer[8:10])
        self.__drawingOnAngles = unpack("<B", buffer[10:11])
        self.__minSpeed = unpack("<B", buffer[11:12])
        self.__HDOP = unpack("<B", buffer[12:13])
        self.__minspeed = unpack("<B", buffer[13:14])
        self.__maxspeed = unpack("<B", buffer[14:15])
        self.__acceleration = unpack("<B", buffer[15:16])
        self.__jump = unpack("<B", buffer[16:17])
        self.__idle = unpack("<B", buffer[17:18])
        self.__courseDeviation = unpack("<B", buffer[18:19])
        
        print("Jump is %d" % self.__jump)

class PacketAnswerCommandSwitchSecurityMode(PacketAnswer):
    """
    Answer on CommandSwitchSecurityMode
    """
    _command = 14
    
    __serviceMessage200 = 0
    
    @property
    def serviceMessage200(self):
        if self._rebuild: self._build()
        return self.__serviceMessage200
    
    def _parseBody(self):
        print("Got service message 200")
        super(PacketAnswerCommandSwitchSecurityMode, self)._parseBody()
        buffer = self.body
        self._command = unpack('<B', buffer[:1])[0]
        
        self.__serviceMessage200 = unpack('<H', buffer[1:3]) 
    

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
            raise Exception('Class for %s is not found' % data)
        return CLASS(data)




import inspect
import sys

def getAnswerClassByNumber(number):
    """
     Returns command class by its number
     @param number: int Number of the command
     @return: Command class
    """
    for name, cls in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(cls) and \
            issubclass(cls, PacketAnswer) and\
                cls._command == number:
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
        self.assertEqual(packet.rawData, b'\x12\x00\x22\x00012896001609129\x05$6')
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

    def test_simpleCommandsPacket(self):
        cmd = CommandGetStatus()
        self.assertEqual(cmd.number, 0)
        self.assertEqual(cmd.rawData, b'\x02\x00\x00\xd0')

        cmd = CommandGetRegisteredIButtons()
        self.assertEqual(cmd.number, 5)
        self.assertEqual(cmd.checksum, 54208)
        self.assertEqual(cmd.rawData, b'\x02\x05\xc0\xd3')

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

    def test_commandChangeDeviceNumber(self):
        cmd = CommandChangeDeviceNumber({
            'deviceNumber': 1056
        })
        self.assertEqual(cmd.number, 2)
        self.assertEqual(cmd.deviceNumber, 1056)
        self.assertEqual(cmd.checksum, 24504)
        self.assertEqual(cmd.rawData, b'\x02\x02\x20\x04\xb8_')
        
        # let's change deviceNumber
        cmd.deviceNumber = 8888
        self.assertEqual(cmd.rawData, b'\x02\x02\xb8"RE')
    
    def test_commandChangeDevicePassword(self):
        cmd = CommandChangeDevicePassword({
            'devicePassword': 36718
        })
            
        self.assertEqual(cmd.number, 3)
        self.assertEqual(cmd.devicePassword, 36718)
        self.assertEqual(cmd.checksum, 22684)
        self.assertEqual(cmd.rawData, b'\x02\x03n\x8f\x9cX')
        
        #test password change
        cmd.devicePassword = 2403
        self.assertEqual(cmd.devicePassword, 2403)
        self.assertEqual(cmd.rawData, b'\x02\x03c\t\x19j')
    
    def test_gprsCommandsPacket(self):
        cmd = CommandSetGprsParams({
            "ip": '127.0.0.1',
            "port": 20200
        })
        self.assertEqual(cmd.number, 4)
        self.assertEqual(cmd.checksum, 10512)
        self.assertEqual(cmd.rawData, b'\x02\x04\x7f\x00\x00\x01\xe8N\x10)')
        # let's change port and ip
        cmd.port = 20201
        cmd.ip = '212.10.222.10'
        self.assertEqual(cmd.rawData, b'\x02\x04\xd4\n\xde\n\xe9N\xdb\x89')
    
    def test_commandAddRemoveKeyNumber(self):
        cmd = CommandAddRemoveKeyNumber({
            "processKeyNumberAction": PROCESS_KEY_NUMBER_ACTION_ADD,
            "processCellNumber": 14,
            "keyNumber": 218875
        })
        
        self.assertEqual(cmd.number, 6)
        
        self.assertEqual(cmd.processKeyNumberAction, PROCESS_KEY_NUMBER_ACTION_ADD)
        self.assertEqual(cmd.processCellNumber, 14)
        self.assertEqual(cmd.keyNumber, 218875)
        self.assertEqual(cmd.checksum, 47393)
        self.assertEqual(cmd.rawData, b'\x02\x06\x0e\xfbV\x03\x00\x00\x00!\xb9')
        #change some data
        cmd.processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_REMOVE
        cmd.processCellNumber = 7
        cmd.keyNumber = 11246
        
        self.assertEqual(cmd.processKeyNumberAction, PROCESS_KEY_NUMBER_ACTION_REMOVE)
        self.assertEqual(cmd.processCellNumber, 7)
        self.assertEqual(cmd.keyNumber, 11246)
        self.assertEqual(cmd.checksum, 62407)
        self.assertEqual(cmd.rawData, b'\x02\x06\x17\xee+\x00\x00\x00\x00\xc7\xf3')
    
    def test_commandAddRemovePhoneNumber(self):
        cmd = CommandAddRemovePhoneNumber({
            "processKeyNumberAction": PROCESS_KEY_NUMBER_ACTION_ADD,
            "processCellNumber": 5,
            "phoneNumber": "2375129873",
            "callSmsCall": CALL_SMS_CALL_SWITCH_TO_VOICE_MENU,
            "callSmsSms": CALL_SMS_SMS_RECEIVE
        })
        self.assertEqual(cmd.number, 8)
        
        self.assertEqual(cmd.processKeyNumberAction, PROCESS_KEY_NUMBER_ACTION_ADD)
        self.assertEqual(cmd.processCellNumber, 5)
        self.assertEqual(cmd.phoneNumber, "2375129873")
        self.assertEqual(cmd.callSmsCall, CALL_SMS_CALL_SWITCH_TO_VOICE_MENU)
        self.assertEqual(cmd.callSmsSms, CALL_SMS_SMS_RECEIVE)
        self.assertEqual(cmd.checksum, 52634)
        self.assertEqual(cmd.rawData,  b'\x02\x08\x052\x11\x9a\xcd')
        
        #change some data
        cmd.processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_REMOVE
        cmd.processCellNumber = 7
        cmd.phoneNumber = "0030070010"
        cmd.callSmsCall = CALL_SMS_CALL_CHANGE_SECURITY
        cmd.callSmsSms = CALL_SMS_SMS_IGNORE
        
        self.assertEqual(cmd.processKeyNumberAction, PROCESS_KEY_NUMBER_ACTION_REMOVE)
        self.assertEqual(cmd.processCellNumber, 7)
        self.assertEqual(cmd.phoneNumber, "0030070010")
        self.assertEqual(cmd.callSmsCall, CALL_SMS_CALL_CHANGE_SECURITY)
        self.assertEqual(cmd.callSmsSms, CALL_SMS_SMS_IGNORE)
        self.assertEqual(cmd.checksum, 31994)
        self.assertEqual(cmd.rawData,  b'\x02\x08\x170 \xfa|')
    
    def test_commandProtocolTypeStructure(self):
        cmd = CommandProtocolTypeStructure({
            "protocolType": 23,
            "protocolStructure": 782357
        })
        self.assertEqual(cmd.number, 9)
        
        self.assertEqual(cmd.protocolType, 23)
        self.assertEqual(cmd.protocolStructure, 782357)
        self.assertEqual(cmd.checksum, 50182)
        self.assertEqual(cmd.rawData,  b'\x02\t\x17\x15\xf0\x0b\x00\x00\x00\x00\x00\x06\xc4')
        
        #change some data
        cmd.protocolType = 51
        cmd.protocolStructure = 213527
        
        self.assertEqual(cmd.protocolType, 51)
        self.assertEqual(cmd.protocolStructure, 213527)
        self.assertEqual(cmd.checksum, 24511)
        self.assertEqual(cmd.rawData, b'\x02\t3\x17B\x03\x00\x00\x00\x00\x00\xbf_')
    
    def test_commandFiltrationDrawingParameters(self):
        cmd = CommandFiltrationDrawingParameters({
            "filterCoordinates": 1,
            "filterStraightPath": 0,
            "filterRestructuring": 1,
            "filterWriteOnEvent": 1,
            "accelerometerSensitivity": 1817,
            "timeToStandby": 5671,
            "timeRecordingStandby": 13295,
            "timeRecordingMoving": 27152,
            "timeRecordingDistance": 108,
            "drawingOnAngles": 17,
            "minSpeed": 201,
            "HDOP": 15,
            "minspeed": 89,
            "maxspeed": 107,
            "acceleration": 26,
            "jump": 51,
            "idle": 11,
            "courseDeviation": 18            
        })
        self.assertEqual(cmd.number, 11)
        
        self.assertEqual(cmd.filterCoordinates, 1)
        self.assertEqual(cmd.filterStraightPath, 0)
        self.assertEqual(cmd.filterRestructuring, 1)
        self.assertEqual(cmd.filterWriteOnEvent, 1)
        self.assertEqual(cmd.accelerometerSensitivity, 1817)
        self.assertEqual(cmd.timeToStandby, 5671)
        self.assertEqual(cmd.timeRecordingStandby, 13295)
        self.assertEqual(cmd.timeRecordingMoving, 27152)
        self.assertEqual(cmd.timeRecordingDistance, 108)
        self.assertEqual(cmd.drawingOnAngles, 17)
        self.assertEqual(cmd.minSpeed, 201)
        self.assertEqual(cmd.HDOP, 15)
        self.assertEqual(cmd.minspeed, 89)
        self.assertEqual(cmd.maxspeed, 107)
        self.assertEqual(cmd.acceleration, 26)
        self.assertEqual(cmd.jump, 51)
        self.assertEqual(cmd.idle, 11)
        self.assertEqual(cmd.courseDeviation, 18)
        self.assertEqual(cmd.checksum, 8476)
        self.assertEqual(cmd.rawData, b"\x02\x0b\xb0\x19\x07'\x16\xef3\x10jl\x11\xc9\x0fYk\x1a\x0b3\x12\x1c!")
        
        #change some data
        
        cmd.filterCoordinates = 0
        cmd.filterStraightPath = 1
        cmd.filterRestructuring = 1
        cmd.filterWriteOnEvent = 0
        cmd.accelerometerSensitivity = 2516
        cmd.timeToStandby = 98
        cmd.timeRecordingStandby = 9761
        cmd.timeRecordingMoving = 18999
        cmd.timeRecordingDistance =  97
        cmd.drawingOnAngles = 11
        cmd.minSpeed = 23
        cmd.HDOP = 31
        cmd.minspeed = 107
        cmd.maxspeed = 204
        cmd.acceleration = 3
        cmd.idle = 71
        cmd.jump = 14
        cmd.courseDeviation = 57
        
        self.assertEqual(cmd.filterCoordinates, 0)
        self.assertEqual(cmd.filterStraightPath, 1)
        self.assertEqual(cmd.filterRestructuring, 1)
        self.assertEqual(cmd.filterWriteOnEvent, 0)
        self.assertEqual(cmd.accelerometerSensitivity, 2516)
        self.assertEqual(cmd.timeToStandby, 98)
        self.assertEqual(cmd.timeRecordingStandby, 9761)
        self.assertEqual(cmd.timeRecordingMoving, 18999)
        self.assertEqual(cmd.timeRecordingDistance, 97)
        self.assertEqual(cmd.drawingOnAngles, 11)
        self.assertEqual(cmd.minSpeed, 23)
        self.assertEqual(cmd.HDOP, 31)
        self.assertEqual(cmd.minspeed, 107)
        self.assertEqual(cmd.maxspeed, 204)
        self.assertEqual(cmd.acceleration, 3)
        self.assertEqual(cmd.idle, 71)
        self.assertEqual(cmd.jump, 14)
        self.assertEqual(cmd.courseDeviation, 57)
        self.assertEqual(cmd.checksum, 50544)
        self.assertEqual(cmd.rawData, b'\x02\x0b`\xd4\tb\x00!&7Ja\x0b\x17\x1fk\xcc\x03G\x0e9p\xc5')

    def test_commandConfigureInputs(self):
        cmd = CommandConfigureInputs({
            "inputActActiveLevel": ACTIVE_LEVEL_LOW_WITH_HYSTERESIS,
            "inputActInputNumber": 9,
            "lowerBorder": 17281,
            "upperBorder": 21817,
            "filterLength": 93
        })
        
        self.assertEqual(cmd.number, 12)
        
        self.assertEqual(cmd.inputActActiveLevel, ACTIVE_LEVEL_LOW_WITH_HYSTERESIS)
        self.assertEqual(cmd.inputActInputNumber, 9)
        self.assertEqual(cmd.lowerBorder, 17281)
        self.assertEqual(cmd.upperBorder, 21817)
        self.assertEqual(cmd.filterLength, 93)
        self.assertEqual(cmd.checksum, 46340)
        self.assertEqual(cmd.rawData, b'\x02\x0cI\x81C9U]\x04\xb5')
        
        #change some data
        cmd.inputActActiveLevel = ACTIVE_LEVEL_FREE
        cmd.inputActInputNumber = 11
        cmd.lowerBorder = 9703
        cmd.upperBorder = 19517
        cmd.filterLength = 27
        
        self.assertEqual(cmd.inputActActiveLevel, ACTIVE_LEVEL_FREE)
        self.assertEqual(cmd.inputActInputNumber, 11)
        self.assertEqual(cmd.lowerBorder, 9703)
        self.assertEqual(cmd.upperBorder, 19517)
        self.assertEqual(cmd.filterLength, 27)
        self.assertEqual(cmd.checksum, 54481)
        self.assertEqual(cmd.rawData, b'\x02\x0c+\xe7%=L\x1b\xd1\xd4')   
    
    def test_command_ConfigureOutputs(self):
        cmd = CommandConfigureOutputs({
            "outputMode": OUTPUT_TURN_ON,
            "outputExitNumber": 3,
            "impulseLength": 145,
            "pauseLength": 112,
            "repeatNumber": 23
        })    
        
        self.assertEqual(cmd.number, 13)
        
        self.assertEqual(cmd.outputMode, OUTPUT_TURN_ON)
        self.assertEqual(cmd.outputExitNumber, 3)
        self.assertEqual(cmd.impulseLength, 145)
        self.assertEqual(cmd.pauseLength, 112)
        self.assertEqual(cmd.repeatNumber, 23)
        self.assertEqual(cmd.checksum, 40732)
        self.assertEqual(cmd.rawData, b'\x02\r\x13\x91p\x17\x1c\x9f')
        
        #change some data
        cmd.outputMode = OUTPUT_IMPULSE
        cmd.outputExitNumber = 7
        cmd.impulseLength = 113
        cmd.pauseLength = 96
        cmd.repeatNumber = 31
        
        self.assertEqual(cmd.outputMode, OUTPUT_IMPULSE)
        self.assertEqual(cmd.outputExitNumber, 7)
        self.assertEqual(cmd.impulseLength, 113)
        self.assertEqual(cmd.pauseLength, 96)
        self.assertEqual(cmd.repeatNumber, 31)
        self.assertEqual(cmd.checksum, 24351)
        self.assertEqual(cmd.rawData, b"\x02\r'q`\x1f\x1f_")
        
    def test_commandSwitchSecurityMode(self):
        cmd = CommandSwitchSecurityMode({
            'securityMode': SECURITY_MODE_IS_ON
        })
        self.assertEqual(cmd.number, 14)
        self.assertEqual(cmd.securityMode, str(SECURITY_MODE_IS_ON))
        self.assertEqual(cmd.checksum, 40981)
        self.assertEqual(cmd.rawData, b'\x02\x0e\x01\x15\xa0')

        cmd.securityMode = SECURITY_MODE_IS_OFF
        self.assertEqual(cmd.securityMode, str(SECURITY_MODE_IS_OFF))
        self.assertEqual(cmd.checksum, 24788)
        self.assertEqual(cmd.rawData, b'\x02\x0e\x00\xd4`')
    
    def test_commandTemporarySecurityParameters(self):
        cmd = CommandTemporarySecurityParameters({
            "enterTime": 23,
            "exitTime": 52,
            "memoryTime": 13,
        })
        
        self.assertEqual(cmd.number, 15)
        
        self.assertEqual(cmd.enterTime, 23)
        self.assertEqual(cmd.exitTime, 52)
        self.assertEqual(cmd.memoryTime, 13)
        self.assertEqual(cmd.checksum, 54585)
        self.assertEqual(cmd.rawData, b'\x02\x0f\x174\r9\xd5')
        
        #change some parameters
        cmd.enterTime = 31
        cmd.exitTime = 67
        cmd.memoryTime = 17
        
        self.assertEqual(cmd.enterTime, 31)
        self.assertEqual(cmd.exitTime, 67)
        self.assertEqual(cmd.memoryTime, 17)
        self.assertEqual(cmd.checksum, 11934)
        self.assertEqual(cmd.rawData, b'\x02\x0f\x1fC\x11\x9e.')
    
    def test_commandVoiceConnectionParameters(self):
        cmd = CommandVoiceConnectionParameters({
            "microphoneGain": 56,
            "speakerGain": 77,
            "autodialDialNumber": 6,
            "voiceMenuVolume": 28
        })
        
        self.assertEqual(cmd.number, 17)
        
        self.assertEqual(cmd.microphoneGain, 56)
        self.assertEqual(cmd.speakerGain, 77)
        self.assertEqual(cmd.autodialDialNumber, 6)
        self.assertEqual(cmd.voiceMenuVolume, 28)
        self.assertEqual(cmd.checksum, 58466)
        self.assertEqual(cmd.rawData, b'\x02\x118M\x06\x1cb\xe4')
        
        #change some parameters
        cmd.microphoneGain = 44
        cmd.speakerGain = 98
        cmd.autodialDialNumber = 8
        cmd.voiceMenuVolume = 82
        
        self.assertEqual(cmd.microphoneGain, 44)
        self.assertEqual(cmd.speakerGain, 98)
        self.assertEqual(cmd.autodialDialNumber, 8)
        self.assertEqual(cmd.voiceMenuVolume, 82)
        self.assertEqual(cmd.checksum, 35282)
        self.assertEqual(cmd.rawData, b'\x02\x11,b\x08R\xd2\x89')
        
        
        
    
    def test_commandSoftwareUpgrade(self):
        cmd = CommandSoftwareUpgrade({
            "ip": '127.0.0.1',
            "port": 20200
        })
        self.assertEqual(cmd.number, 19)
        
        self.assertEqual(cmd.port, 20200)
        self.assertEqual(cmd.ip, '127.0.0.1')
        self.assertEqual(cmd.checksum, 10359)
        self.assertEqual(cmd.rawData, b'\x02\x13\x7f\x00\x00\x01\xe8Nw(')
        # let's change port and ip
        cmd.port = 20201
        cmd.ip = '212.10.222.10'
        self.assertEqual(cmd.rawData, b'\x02\x13\xd4\n\xde\n\xe9N\xbc\x88')
    
    def test_getImageCommandsPacket(self):
        cmd = CommandGetImage({
            'type': IMAGE_RESOLUTION_640x480
        })
        self.assertEqual(cmd.number, 20)
        self.assertEqual(cmd.rawData, b'\x02\x14\x03\x9f\x01')

        cmd.type = IMAGE_PACKET_CONFIRM_OK
        self.assertEqual(cmd.rawData, b'\x02\x14\x10\xde\xcc')
    
    def test_commandGetConfiguration(self):
        cmd = CommandGetConfiguration({
            'configurationNumber': 5
        })
        self.assertEqual(cmd.number, 21)
        self.assertEqual(cmd.configurationNumber, 5)
        self.assertEqual(cmd.checksum, 37662)
        self.assertEqual(cmd.rawData, b'\x02\x15\x05\x1e\x93')

        cmd.configurationNumber = 7
        self.assertEqual(cmd.configurationNumber, 7)
        self.assertEqual(cmd.checksum, 21151)
        self.assertEqual(cmd.rawData, b'\x02\x15\x07\x9fR')
    
    def test_commandWriteConfiguration(self):
        cmd = CommandWriteConfiguration({
            'configurationNumber': 11,
            'configurationSize': 7,
            'configurationData': "abc1234"
        })
        self.assertEqual(cmd.number, 22)
        self.assertEqual(cmd.configurationNumber, 11)
        self.assertEqual(cmd.configurationSize, 7)
        self.assertEqual(cmd.configurationData, "abc1234")
        self.assertEqual(cmd.checksum, 31274)
        self.assertEqual(cmd.rawData, b'\x02\x16\x0b\x07\x00*z')
        
        #change some data
        cmd.configurationNumber = 12
        cmd.configurationSize = 8
        cmd.configurationData = "12345abc"
        
        self.assertEqual(cmd.configurationNumber, 12)
        self.assertEqual(cmd.configurationSize, 8)
        self.assertEqual(cmd.configurationData, "12345abc")
        self.assertEqual(cmd.checksum, 19358)
        self.assertEqual(cmd.rawData, b'\x02\x16\x0c\x08\x00\x9eK')
        
    
    def test_commandSwitchToNewSim(self):
        cmd = CommandSwitchToNewSim({
            'simNumber': 217
        })
        self.assertEqual(cmd.number, 23)
        self.assertEqual(cmd.simNumber, '217')
        self.assertEqual(cmd.checksum, 27166)
        self.assertEqual(cmd.rawData, b'\x02\x17\xd9\x1ej')

        cmd.simNumber = 119
        self.assertEqual(cmd.simNumber, '119')
        self.assertEqual(cmd.checksum, 54943)
        self.assertEqual(cmd.rawData, b'\x02\x17w\x9f\xd6')
    
    def test_commandSwitchToConfigurationServer(self):
        cmd = CommandSwitchToConfigurationServer({
            "ip": '127.0.0.1',
            "port": 20200
        })
        self.assertEqual(cmd.number, 24)
        self.assertEqual(cmd.port, 20200)
        self.assertEqual(cmd.ip, '127.0.0.1')
        self.assertEqual(cmd.checksum, 59597)
        # let's change port and ip
        cmd.port = 20201
        cmd.ip = '212.10.222.10'
        self.assertEqual(cmd.rawData, b'\x02\x18\xd4\n\xde\n\xe9N\x06H')
    
    def test_commandAllowDisallowSimAutoswitching(self):
        cmd = CommandAllowDisallowSimAutoswitching({
            'simAutoswitchingIsAllowed': SIM_AUTOSWITCHING_IS_ALLOWED
        })
        self.assertEqual(cmd.number, 25)
        self.assertEqual(cmd.simAutoswitchingIsAllowed, str(SIM_AUTOSWITCHING_IS_ALLOWED))
        self.assertEqual(cmd.checksum, 20506)
        self.assertEqual(cmd.rawData, b'\x02\x19\x01\x1aP')

        cmd.simAutoswitchingIsAllowed = SIM_AUTOSWITCHING_IS_DISALLOWED
        self.assertEqual(cmd.simAutoswitchingIsAllowed, str(SIM_AUTOSWITCHING_IS_DISALLOWED))
        self.assertEqual(cmd.checksum, 37083)
        self.assertEqual(cmd.rawData, b'\x02\x19\x00\xdb\x90')


"""    
Command()

commands["CommandProtocolTypeStructure"]
obj = commands.CommandProtocolTypeStructure()




commands_list = ["CommandSetGprsParameters", 4, 654, [["ip", "ip"], ["port", "H"]]]


#ip, B, 4B
commands_dict = {
    "name": " CommandSetGprsParameters",
    "number": 4,
    "fields": [{
        "name": "ip",
        "type": "ip"
    }, {
        "name": "port",
        "type": "H"
    }]
}


generate_classes(commands_list)
"""












    
