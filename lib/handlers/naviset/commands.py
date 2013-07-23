# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Naviset commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory
from lib.handlers.naviset.packets import *

# ---------------------------------------------------------------------------

class NavisetCommand(AbstractCommand, NavisetBase):
    """
     Naviset command packet
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

    def _parseHeader(self):
        # read header and command number
        unpacked = unpack('<BB', self._head)
        self._header = unpacked[0]
        self._number = unpacked[1]
        headerCode = 0x02
        if self._header != headerCode:
            raise Exception('Incorrect command packet! ' +\
                            str(self._header) + ' (given) != ' +\
                            str(headerCode) + ' (must be)')

    def _buildHead(self):
        data = b''
        data += pack('<B', self._header)
        data += pack('<B', self._number)
        return data

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        if transport == "tcp":
            return self.rawData
        return []

# ---------------------------------------------------------------------------

class NavisetCommandConfigure(NavisetCommand, AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = True
    """ False if protocol doesn't support dns hostname (only ip-address) """

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        config = self._initiationConfig
        password = '1234'
        if transport == "sms":
            command0 = 'COM3 ' + password + ',' + config['host'] + \
                ',' + str(config['port'])
            command1 = 'COM13 '  + password + ',1' + \
                ',' + config['gprs']['apn'] + \
                ',' + config['gprs']['username'] + \
                ',' + config['gprs']['password'] + '#'
            return [{
                "message": command0
            }, {
                "message": command1
            }]
        else:
            return super(NavisetCommandConfigure, self).getData(transport)

# ---------------------------------------------------------------------------

class NavisetCommandGetStatus(NavisetCommand):
    alias = 'get_status'
    _number = 0

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM0 " + password
            }]
        else:
            return super(NavisetCommandGetStatus, self).getData(transport)

# ---------------------------------------------------------------------------

class NavisetCommandGetImei(NavisetCommand):
    alias = 'get_gsm_module_imei'
    _number = 1

# ---------------------------------------------------------------------------

class NavisetCommandGetRegisteredIButtons(NavisetCommand):
    alias = 'get_registered_ibuttons'
    _number = 5

# ---------------------------------------------------------------------------

class NavisetCommandGetPhones(NavisetCommand):
    alias = 'get_phone_numbers'
    _number = 7

# ---------------------------------------------------------------------------

class NavisetCommandGetTrackParams(NavisetCommand):
    alias = 'get_tracker_parameters'
    _number = 10

# ---------------------------------------------------------------------------

class NavisetCommandRemoveTrackFromBuffer(NavisetCommand):
    alias = 'remove_track_from_buffer'
    _number = 16

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM97 " + password
            }]
        else:
            return super(NavisetCommandRemoveTrackFromBuffer,
                self).getData(transport)

# ---------------------------------------------------------------------------

class NavisetCommandRestart(NavisetCommand):
    alias = 'restart_tracker'
    _number = 18

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM98 " + password
            }]
        else:
            return super(NavisetCommandRestart, self).getData(transport)

# ---------------------------------------------------------------------------

class NavisetCommandChangeDeviceNumber(NavisetCommand):
    """
     Change device number
    """
    alias = 'change_device_number'
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

class NavisetCommandChangeDevicePassword(NavisetCommand):
    """
    Change device password
    """
    alias = 'change_device_password'
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

class NavisetCommandSetGprsParams(NavisetCommand):
    """
     Change device GPRS params
    """
    alias = 'set_gprs_parameters'
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
        if 0 <= value <= 0xFFFF:
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

class NavisetCommandAddRemoveKeyNumber(NavisetCommand):
    """
    Adds or removes device key for selected cell.
    """
    alias = 'add_remove_keynumber'
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
        processPacked = (
            16 * self.processKeyNumberAction + self.processCellNumber
            )
        data += pack('<B', processPacked)
        data += pack('<Q', self.__keyNumber)[:-2]
        return data

CALL_SMS_CALL_RECEIVE = 0
CALL_SMS_CALL_SWITCH_TO_VOICE_MENU = 1
CALL_SMS_CALL_CHANGE_SECURITY = 2
CALL_SMS_CALL_STOP = 3

CALL_SMS_SMS_IGNORE = 0
CALL_SMS_SMS_RECEIVE = 1

class NavisetCommandAddRemovePhoneNumber(NavisetCommand):
    """
    Add or remove phone number and change its parameters
    """
    alias = 'add_remove_phone_number'
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
        self.processKeyNumberAction = (
            params['processKeyNumberAction'] or PROCESS_KEY_NUMBER_ACTION_ADD
        )
        self.processCellNumber = params['processCellNumber'] or 0
        self.phoneNumber = params['phoneNumber'] or "0000000000"
        self.callSmsCall = params['callSmsCall'] or CALL_SMS_CALL_RECEIVE
        self.callSmsSms = params['callSmsSms'] or CALL_SMS_SMS_IGNORE

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
        self.__phoneNumber = value
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
        processPacked = (
            16 * self.processKeyNumberAction + self.processCellNumber
            )
        data += pack('<B', processPacked)
        phone = self.phoneNumber.encode()[:10]
        while len(phone) < 10: phone = b'0' + phone
        data += phone
        callSmsPacked = 16 * self.callSmsCall + self.callSmsSms
        data += pack('<B', callSmsPacked)
        return data

class NavisetCommandProtocolTypeStructure(NavisetCommand):
    """
    Sets protocol type and structure
    """
    alias = 'set_protocol_type_structure'
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


class NavisetCommandFiltrationDrawingParameters(NavisetCommand):
    """
    Sets filtration and drawing
    """
    alias = 'set_filtration_drawing_parameters'
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
        filterPacked = (
            128 * self.__filterCoordinates + 64 * self.__filterStraightPath
            + 32 * self.__filterRestructuring + 16 * self.__filterWriteOnEvent
            )
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

class NavisetCommandConfigureInputs(NavisetCommand):
    """
    Configures device inputs.
    """
    alias = 'configure_inputs'
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
        inputActPacked = (
            16 * self.__inputActActiveLevel + self.__inputActInputNumber
            )
        data += pack('<B', inputActPacked)
        data += pack('<H', self.__lowerBorder)
        data += pack('<H', self.__upperBorder)
        data += pack('<B', self.__filterLength)
        return data

OUTPUT_TURN_OFF = 0
OUTPUT_TURN_ON = 1
OUTPUT_IMPULSE = 2


class NavisetCommandConfigureOutputs(NavisetCommand):
    """
    Configures device outputs.
    """
    alias = 'configure_outputs'
    _number = 13

    # private params
    __outputMode = OUTPUT_TURN_OFF
    __outputNumber = 0
    __impulseLength = 0
    __pauseLength = 0
    __repeatNumber = 0

    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """

        self.outputMode = int(dictCheckItem(params,
            'outputMode', OUTPUT_TURN_OFF))
        self.outputNumber = int(dictCheckItem(params, 'outputNumber', 0))
        self.impulseLength = int(dictCheckItem(params, 'impulseLength', 0))
        self.pauseLength = int(dictCheckItem(params, 'pauseLength', 0))
        self.repeatNumber = int(dictCheckItem(params, 'repeatNumber', 0))


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
    def outputNumber(self):
        if self._rebuild: self._build()
        return self.__outputNumber

    @outputNumber.setter
    def outputNumber(self, value):
        if 0 <= value <= 0xF:
            self.__outputNumber = value
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
        outputPacked = 16 * self.__outputMode + self.__outputNumber
        data += pack('<B', outputPacked)
        data += pack('<B', self.__impulseLength)
        data += pack('<B', self.__pauseLength)
        data += pack('<B', self.__repeatNumber)
        return data

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM7 " + password + ',' +\
                     str(self.outputNumber + 1) + ',' + str(self.outputMode)
            }]
        else:
            return super(NavisetCommandConfigureOutputs,
                self).getData(transport)

class CommandDeactivateDigitalOutput(NavisetCommandConfigureOutputs):
    """
    Activates digital output by number, other parameters are not required
    """
    alias = 'deactivate_digital_output'

    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.outputMode = OUTPUT_TURN_OFF
        self.outputNumber = int(dictCheckItem(params, 'outputNumber', 0))
        self.impulseLength = 0
        self.pauseLength = 0
        self.repeatNumber = 0

class CommandActivateDigitalOutput(NavisetCommandConfigureOutputs):
    """
    Activates digital output by number, other parameters are not required
    """
    alias = 'activate_digital_output'

    def setParams(self, params):
        """
        Initialize command with params
        @param params:
        @return:
        """
        self.outputMode = OUTPUT_TURN_ON
        self.outputNumber = int(dictCheckItem(params, 'outputNumber', 0))
        self.impulseLength = 0
        self.pauseLength = 0
        self.repeatNumber = 0

SECURITY_MODE_IS_OFF = 0
SECURITY_MODE_IS_ON = 1

class NavisetCommandSwitchSecurityMode(NavisetCommand):
    """
     Command for switching security number
    """
    alias = 'switch_security_mode'
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

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            if self.securityMode == 0:
                return [{"message": "COM10 " + password}]
            else:
                return [{"message": "COM11 " + password}]
        else:
            return super(NavisetCommandSwitchSecurityMode,
                         self).getData(transport)


class NavisetCommandArmTimeParameters(NavisetCommand):
    """
     Command for setting arm time parameters
    """
    alias = 'set_arm_time_parameters'
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

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM4 " + password + "," + str(self.enterTime) + \
                    "," + str(self.exitTime) + "," + str(self.memoryTime)
            }]
        else:
            return super(NavisetCommandArmTimeParameters,
                self).getData(transport)


class NavisetCommandVoiceConnectionParameters(NavisetCommand):
    """
     Command for setting voice connection parameters
    """
    alias = 'set_voice_connection_parameters'
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

class NavisetCommandSoftwareUpgrade(NavisetCommand):
    """
     Change device GPRS params
    """
    alias = 'upgrade_software'
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

class NavisetCommandGetImage(NavisetCommand):
    """
     Command for image receiving/confirmation
    """
    alias = 'get_image'
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

class NavisetCommandGetConfiguration(NavisetCommand):
    """
     Command for receiving configuration
    """
    alias = 'get_configuration'
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

class NavisetCommandWriteConfiguration(NavisetCommand):
    """
     Command for writing configuration
    """
    alias = 'write_configuration'
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


class NavisetCommandSwitchToNewSim(NavisetCommand):
    """
     Command for switching to new SIM number
    """
    alias = 'switch_to_new_sim'
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

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM12 " + password + ',' + self.simNumber
            }]
        else:
            return super(NavisetCommandSwitchToNewSim, self).getData(transport)


class NavisetCommandSwitchToConfigurationServer(NavisetCommand):
    """
     Make device connect to specified configuration server
    """
    alias = 'connect_to_configuration_server'
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

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM5 " + password + ',' + \
                    self.ip + ',' + str(self.port)
            }]
        else:
            return super(NavisetCommandSwitchToConfigurationServer,
                self).getData(transport)

# ---------------------------------------------------------------------------


SIM_AUTOSWITCHING_IS_DISALLOWED = 0
SIM_AUTOSWITCHING_IS_ALLOWED = 1

class NavisetCommandAllowDisallowSimAutoswitching(NavisetCommand):
    """
     Command for switching to new SIM number
    """
    alias = 'toggle_sim_autoswitching'
    _number = 25

    # private params
    __simAutoswitchingIsAllowed = SIM_AUTOSWITCHING_IS_DISALLOWED

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.simAutoswitchingIsAllowed = (
            params['simAutoswitchingIsAllowed'] or 0)

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

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        password = '1234'
        if transport == "sms":
            return [{
                "message": "COM8 " + password + ',' +\
                   str(self.simAutoswitchingIsAllowed)
            }]
        else:
            return super(NavisetCommandAllowDisallowSimAutoswitching,
                self).getData(transport)

# ---------------------------------------------------------------------------

class CommandFactory(AbstractCommandFactory):
    """
     Command factory
    """
    module = __name__

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        self.factory = CommandFactory()

    def test_packetData(self):
        cmd = self.factory.getInstance({
            'command': 'configure',
            'params': {
                "identifier": "0123456789012345",
                "host": "trx.maprox.net",
                "port": 21200
            }
        })
        self.assertEqual(cmd.getData('sms'), [
            {'message': 'COM3 1234,trx.maprox.net,21200'},
            {'message': 'COM13 1234,1,,,#'}
        ])

    def test_simpleCommandsPacket(self):
        cmd = NavisetCommandGetStatus()
        self.assertEqual(cmd.number, 0)
        self.assertEqual(cmd.rawData, b'\x02\x00\x00\xd0')

        cmd = NavisetCommandGetRegisteredIButtons()
        self.assertEqual(cmd.number, 5)
        self.assertEqual(cmd.checksum, 54208)
        self.assertEqual(cmd.rawData, b'\x02\x05\xc0\xd3')

    def test_commandChangeDeviceNumber(self):
        cmd = NavisetCommandChangeDeviceNumber({
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
        cmd = NavisetCommandChangeDevicePassword({
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
        cmd = NavisetCommandSetGprsParams({
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
        cmd = NavisetCommandAddRemoveKeyNumber({
            "processKeyNumberAction": PROCESS_KEY_NUMBER_ACTION_ADD,
            "processCellNumber": 14,
            "keyNumber": 218875
        })

        self.assertEqual(cmd.number, 6)

        self.assertEqual(cmd.processKeyNumberAction,
                         PROCESS_KEY_NUMBER_ACTION_ADD)
        self.assertEqual(cmd.processCellNumber, 14)
        self.assertEqual(cmd.keyNumber, 218875)
        self.assertEqual(cmd.checksum, 47393)
        self.assertEqual(cmd.rawData, b'\x02\x06\x0e\xfbV\x03\x00\x00\x00!\xb9')
        #change some data
        cmd.processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_REMOVE
        cmd.processCellNumber = 7
        cmd.keyNumber = 11246

        self.assertEqual(cmd.processKeyNumberAction,
                         PROCESS_KEY_NUMBER_ACTION_REMOVE)
        self.assertEqual(cmd.processCellNumber, 7)
        self.assertEqual(cmd.keyNumber, 11246)
        self.assertEqual(cmd.checksum, 62407)
        self.assertEqual(cmd.rawData,
                         b'\x02\x06\x17\xee+\x00\x00\x00\x00\xc7\xf3')

    def test_commandAddRemovePhoneNumber(self):
        cmd = NavisetCommandAddRemovePhoneNumber({
            "processKeyNumberAction": PROCESS_KEY_NUMBER_ACTION_ADD,
            "processCellNumber": 5,
            "phoneNumber": "2375129873",
            "callSmsCall": CALL_SMS_CALL_SWITCH_TO_VOICE_MENU,
            "callSmsSms": CALL_SMS_SMS_RECEIVE
        })
        self.assertEqual(cmd.number, 8)

        self.assertEqual(cmd.processKeyNumberAction,
                         PROCESS_KEY_NUMBER_ACTION_ADD)
        self.assertEqual(cmd.processCellNumber, 5)
        self.assertEqual(cmd.phoneNumber, "2375129873")
        self.assertEqual(cmd.callSmsCall, CALL_SMS_CALL_SWITCH_TO_VOICE_MENU)
        self.assertEqual(cmd.callSmsSms, CALL_SMS_SMS_RECEIVE)
        self.assertEqual(cmd.checksum, 21470)
        self.assertEqual(cmd.rawData,  b'\x02\x08\x052375129873\x11\xdeS')

        #change some data
        cmd.processKeyNumberAction = PROCESS_KEY_NUMBER_ACTION_REMOVE
        cmd.processCellNumber = 7
        cmd.phoneNumber = "0030070010"
        cmd.callSmsCall = CALL_SMS_CALL_CHANGE_SECURITY
        cmd.callSmsSms = CALL_SMS_SMS_IGNORE

        self.assertEqual(cmd.processKeyNumberAction,
                         PROCESS_KEY_NUMBER_ACTION_REMOVE)
        self.assertEqual(cmd.processCellNumber, 7)
        self.assertEqual(cmd.phoneNumber, "0030070010")
        self.assertEqual(cmd.callSmsCall, CALL_SMS_CALL_CHANGE_SECURITY)
        self.assertEqual(cmd.callSmsSms, CALL_SMS_SMS_IGNORE)
        self.assertEqual(cmd.checksum, 61952)
        self.assertEqual(cmd.rawData,  b'\x02\x08\x170030070010 \x00\xf2')

    def test_commandProtocolTypeStructure(self):
        cmd = NavisetCommandProtocolTypeStructure({
            "protocolType": 23,
            "protocolStructure": 782357
        })
        self.assertEqual(cmd.number, 9)

        self.assertEqual(cmd.protocolType, 23)
        self.assertEqual(cmd.protocolStructure, 782357)
        self.assertEqual(cmd.checksum, 50182)
        self.assertEqual(cmd.rawData,
                         b'\x02\t\x17\x15\xf0\x0b\x00\x00\x00\x00\x00\x06\xc4')

        #change some data
        cmd.protocolType = 51
        cmd.protocolStructure = 213527

        self.assertEqual(cmd.protocolType, 51)
        self.assertEqual(cmd.protocolStructure, 213527)
        self.assertEqual(cmd.checksum, 24511)
        self.assertEqual(cmd.rawData,
                         b'\x02\t3\x17B\x03\x00\x00\x00\x00\x00\xbf_')

    def test_commandFiltrationDrawingParameters(self):
        cmd = NavisetCommandFiltrationDrawingParameters({
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
        self.assertEqual(cmd.rawData,
            b"\x02\x0b\xb0\x19\x07'\x16\xef3" +
            b"\x10jl\x11\xc9\x0fYk\x1a\x0b3\x12\x1c!")

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
        self.assertEqual(cmd.rawData,
            b'\x02\x0b`\xd4\tb\x00!&7Ja\x0b' +
            b'\x17\x1fk\xcc\x03G\x0e9p\xc5')

    def test_commandConfigureInputs(self):
        cmd = NavisetCommandConfigureInputs({
            "inputActActiveLevel": ACTIVE_LEVEL_LOW_WITH_HYSTERESIS,
            "inputActInputNumber": 9,
            "lowerBorder": 17281,
            "upperBorder": 21817,
            "filterLength": 93
        })

        self.assertEqual(cmd.number, 12)

        self.assertEqual(cmd.inputActActiveLevel,
                         ACTIVE_LEVEL_LOW_WITH_HYSTERESIS)
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
        cmd = NavisetCommandConfigureOutputs({
            "outputMode": OUTPUT_TURN_ON,
            "outputNumber": 3,
            "impulseLength": 145,
            "pauseLength": 112,
            "repeatNumber": 23
        })

        self.assertEqual(cmd.number, 13)

        self.assertEqual(cmd.outputMode, OUTPUT_TURN_ON)
        self.assertEqual(cmd.outputNumber, 3)
        self.assertEqual(cmd.impulseLength, 145)
        self.assertEqual(cmd.pauseLength, 112)
        self.assertEqual(cmd.repeatNumber, 23)
        self.assertEqual(cmd.checksum, 40732)
        self.assertEqual(cmd.rawData, b'\x02\r\x13\x91p\x17\x1c\x9f')

        #change some data
        cmd.outputMode = OUTPUT_IMPULSE
        cmd.outputNumber = 7
        cmd.impulseLength = 113
        cmd.pauseLength = 96
        cmd.repeatNumber = 31

        self.assertEqual(cmd.outputMode, OUTPUT_IMPULSE)
        self.assertEqual(cmd.outputNumber, 7)
        self.assertEqual(cmd.impulseLength, 113)
        self.assertEqual(cmd.pauseLength, 96)
        self.assertEqual(cmd.repeatNumber, 31)
        self.assertEqual(cmd.checksum, 24351)
        self.assertEqual(cmd.rawData, b"\x02\r'q`\x1f\x1f_")

    def test_commandSwitchSecurityMode(self):
        cmd = NavisetCommandSwitchSecurityMode({
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
        cmd = NavisetCommandArmTimeParameters({
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
        cmd = NavisetCommandVoiceConnectionParameters({
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
        cmd = NavisetCommandSoftwareUpgrade({
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
        cmd = NavisetCommandGetImage({
            'type': IMAGE_RESOLUTION_640x480
        })
        self.assertEqual(cmd.number, 20)
        self.assertEqual(cmd.rawData, b'\x02\x14\x03\x9f\x01')

        cmd.type = IMAGE_PACKET_CONFIRM_OK
        self.assertEqual(cmd.rawData, b'\x02\x14\x10\xde\xcc')

    def test_commandGetConfiguration(self):
        cmd = NavisetCommandGetConfiguration({
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
        cmd = NavisetCommandWriteConfiguration({
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
        cmd = NavisetCommandSwitchToNewSim({
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
        cmd = NavisetCommandSwitchToConfigurationServer({
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
        cmd = NavisetCommandAllowDisallowSimAutoswitching({
            'simAutoswitchingIsAllowed': SIM_AUTOSWITCHING_IS_ALLOWED
        })
        self.assertEqual(cmd.number, 25)
        self.assertEqual(cmd.simAutoswitchingIsAllowed,
                         str(SIM_AUTOSWITCHING_IS_ALLOWED))
        self.assertEqual(cmd.checksum, 20506)
        self.assertEqual(cmd.rawData, b'\x02\x19\x01\x1aP')

        cmd.simAutoswitchingIsAllowed = SIM_AUTOSWITCHING_IS_DISALLOWED
        self.assertEqual(cmd.simAutoswitchingIsAllowed,
                         str(SIM_AUTOSWITCHING_IS_DISALLOWED))
        self.assertEqual(cmd.checksum, 37083)
        self.assertEqual(cmd.rawData, b'\x02\x19\x00\xdb\x90')

    def test_commandsFactory1(self):
        cmd = self.factory.getInstance({
            'command': 'restart_tracker',
            'params': {}
        })
        self.assertEqual(cmd.rawData, b'\x02\x12\x80\xdd')
        cmd = self.factory.getInstance({'command': 'restart_tracker'})
        self.assertEqual(cmd.getData('sms'), [{
            'message': 'COM98 1234'
        }])
        cmd = self.factory.getInstance({'command': 'get_status'})
        self.assertEqual(cmd.getData('sms'), [{
            'message': 'COM0 1234'
        }])
