# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat base class for other Globalsat protocols
@copyright 2009-2012, Maprox LLC
"""

import re
import json
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from kernel.database import db
from lib.handler import AbstractHandler
from lib.geo import Geo

class GlobalsatHandler(AbstractHandler):
  """
   Base handler for Globalsat protocol
  """

  confSectionName = "globalsat.protocolname"
  reportFormat = "SPRXYAB27GHKLMmnaefghio*U!"
  commandStart = "GSS,{0},3,0"

  re_patterns = {
    'line': '(?P<line>(?P<head>GS\w){fields})\*(?P<checksum>\w+)!',
    'field': ',(?P<{field}>{value})',
    'unknownField': '[\w\.]+',
    'service': {
      'I': '\w+',
      'T': '[0-3]',
      'S': '[1-9]?\d'
    },
    'report': {
      'A': '[1-3]',
      'B': '\d{6},\d{6}',
      'C': '\d{6},\d{6}',
      '1': '[EW]\d{3}\.\d{6}',
      '2': '[EW]\d{5}\.\d{4}',
      '3': '[+-]\d{9}',
      '6': '[NS]\d{2}\.\d{6}',
      '7': '[NS]\d{4}\.\d{4}',
      '8': '[+-]\d{8}',
      'G': '\d+',
      'H': '\d+(\.\d+)?',
     #'I': '',
     #'J': '',
      'K': '\d+',
      'L': '\d+',
      'M': '\d+(\.\d+)?',
      'P': '[0-9A-F]{2}',
     #'Z': '',
     #'Q': '',
      'R': '\w',
      'S': '\w+',
     #'T': '',
     #'U': '',
     #'V': '',
     #'W': '',
      'X': '[\w\.]+',
      'Y': '\w{4}',
      'a': '\d+',
      'e': '\d+',
      'f': '\d+',
      'g': '\d+',
      'h': '\d+',
      'i': '\d+',
      'm': '\d+',
      'n': '(\w+|\d+%)',
      'o': '\d+',
     #'s': ''
    },
    'search_config': 'GSs,(?P<uid>\w+),(?P<status>\d+),(?P<order>\d+),(?P<data>.*)\*[a-f\d]{1,2}\!',
    'search_uid': 'GS\w,(?P<uid>\w+)'
  }

  re_compiled = {
    'service': None,
    'report': None,
    'search_uid': None,
    'search_config': None
  }

  re_volts = re.compile('(\d+)mV')
  re_percents = re.compile('(\d+)%')
  re_number = re.compile('(\d+)')

  def __init__(self, store, thread):
    """ Constructor """
    AbstractHandler.__init__(self, store, thread)

    """ Options for Globalsat """
    self.default_options.update({
      # SOS Report count
      # 0 = None, 1 = SMS, 2 = TCP, 3 = SMS and TCP, 4 = UDP
      'H0': '3',
      # SOS Max number of SMS report for each phone number
      'H1': '1',
      # SOS Report interval
      'H2': '30',
      # SOS Max number of GPRS report (0=continues until
      # dismissed via GSC,[IMEI],Na*QQ!)
      'H3': '1',
      # Don't wait acknowledgement from server, dont't send one
      'A0': '0',
      'A1': '0',
      # Turn off voice monitoring
      'V0': '0'
    })

  @classmethod
  def truncateChecksum(cls, value):
    """
     Truncates checksum part from value string
     @param value: value string
     @return: truncated string without checksum part
    """
    return re.sub('\*(\w{1,4})!', '', value)

  @classmethod
  def getChecksum(cls, data):
    """
     Returns the data checksum
     @param data: data string
     @return: hex string checksum
    """
    csum = 0
    for c in data:
        csum ^= ord(c)
    hex_csum = "%02X" % csum
    return hex_csum

  @classmethod
  def addChecksum(cls, data, fmt = "{d}*{c}!"):
    """
     Adds checksum to a data string
     @param data: data string
     @return: data, containing checksum part
    """
    return str.format(fmt, d = data, c = cls.getChecksum(data))

  def __getReportFormat(self):
    """
     Gets the format for report message.
     I suggest that in future here should be code, which would ask
     database for settings of the connecting device (by uid)
     and, if there is no settings, ask device (by socket connection)
     for it's configuration parameters.
     By now we will read settings from server config file.
    """
    if conf.has_section(self.confSectionName):
      section = conf[self.confSectionName]
      self.reportFormat = self.truncateChecksum(section.get(
        "defaultReportFormat", self.reportFormat))

  def getRawReportFormat(self):
    """
     Gets the format for report message.
    """
    if conf.has_section(self.confSectionName):
      section = conf[self.confSectionName]
      return section.get("defaultReportFormat", self.reportFormat)
    return self.reportFormat

  def __compileRegularExpressions(self):
    """
     Compiling of regular expressions
    """
    # Let's start with report format
    p = self.re_patterns
    fieldsStr = ""
    for char in self.reportFormat:
      pattern = p['unknownField']
      if char in p['report']:
        pattern = p['report'][char]
      # We need to avoid digital names of groups
      fieldName = char
      if char.isdigit():
        fieldName = "d" + char
      fieldsStr += str.format(p['field'], field = fieldName, value = pattern)
    line = str.format(p['line'], fields = fieldsStr)
    self.re_compiled['report'] = re.compile(line, flags = re.IGNORECASE)
    # Compiling the pattern for uid searching
    self.re_compiled['search_uid'] = \
      re.compile(p['search_uid'], flags = re.IGNORECASE)
    self.re_compiled['search_config'] = re.compile(p['search_config'])
    return self

  def prepare(self):
    """
     Preparing for data transfer
    """
    self.__getReportFormat()
    self.__compileRegularExpressions()
    return self

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    packet = {}
    packet['sensors'] = {}
    for char in data:
      value = data[char]
      # IMEI / UID
      if   char == "S": packet['uid'] = value
      # TIME
      elif char == "B":
        dt = datetime.strptime(value, '%d%m%y,%H%M%S')
        packet['time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
      # COORD
      elif char in ("d1", "d2", "d3"):
        packet['longitude'] = Geo.getLongitude(value)
      elif char in ("d6", "d7", "d8"):
        packet['latitude'] = Geo.getLatitude(value)
      # ALTITUDE
      elif char == "G":
        packet['altitude'] = float(value)
      # SPEED (knots)
      elif char == "H":
        packet['speed'] = 1.852 * float(value)
      # SPEED (km/hr)
      elif char == "I":
        packet['speed'] = value
      # SPEED (mile/hr)
      elif char == "J":
        packet['speed'] = 1.609344 * float(value)
      # Satellites count
      elif char == "L":
        packet['satellitescount'] = int(value)
      # Azimuth - driving direction
      elif char == "K":
        packet['azimuth'] = float(value)
      # Odometer
      elif char == "i":
        packet['odometer'] = float(value)
        packet['sensors']['odometer'] = packet['odometer']
      # HDOP (Horizontal Dilution of Precision)
      elif char == "M":
        packet['hdop'] = float(value)
      # Extracting movement sensor from report type. Have lower priority than actual movement sensor
      elif char == "R":
        if not 'movementsensor' in packet:
          packet['movementsensor'] = int(value != '4' and value != 'F' and value != 'E')
      # Extracting movement sensor value and ACC
      elif char == "Y":
        # Tracker sends value as HEX string
        dec = int(value, 16)
        packet['movementsensor'] = (dec >> 7) % 2
       # ACC Sensor
        packet['sensors']['acc'] = (dec >> 13) % 2
       # Digital inputs
        packet['sensors']['digital_input1'] = (dec >> 1) % 2
        packet['sensors']['digital_input2'] = (dec >> 2) % 2
        packet['sensors']['digital_input3'] = (dec >> 3) % 2
       # Digital outputs
        packet['sensors']['digital_output1'] = (dec >> 9) % 2
        packet['sensors']['digital_output2'] = (dec >> 10) % 2
        packet['sensors']['digital_output3'] = (dec >> 11) % 2
      # Signalization status
      elif char == "P":
        dec = int(value, 16)
        packet['sensors']['sos'] = dec % 2
        packet['sensors']['nogpsantenna'] = (dec >> 2) % 2
        packet['sensors']['battery_disconnect'] = (dec >> 6) % 2
        packet['sensors']['battery_discharge'] = (dec >> 7) % 2
      # Counters
      elif char == "e":
        packet['sensors']['counter0'] = float(value)
      elif char == "f":
        packet['sensors']['counter1'] = float(value)
      elif char == "g":
        packet['sensors']['counter2'] = float(value)
      elif char == "h":
        packet['sensors']['counter3'] = float(value)
      # Analog input 0
      elif char == "a":
        packet['sensors']['analog_input0'] = float(value)
      elif char == "n" or char == "N":
        if (self.re_volts.match(value)):
          packet['batterylevel'] = 1
        elif (self.re_percents.match(value)):
          percents = float(self.re_percents.search(value).group(1)) / 100
          packet['batterylevel'] = percents
        elif (self.re_number.match(value)):
          percents = int(value) / 100
          packet['batterylevel'] = percents
    return packet

  def translateConfig(self, data):
    """
     Translate gps-tracker config data to observer format
     @param data: {string[]} data from gps-tracker
    """
    send = {}
    send['raw'] = ','.join(data)

    tmp_options = send['raw'].split(',')
    options = {}
    for option in tmp_options:
      option = option.split('=')
      key = option[:1][0]
      del option[:1]
      value = '='.join(option)
      options[key] = value

    send['freq_mov'] = options['R1']
    send['freq_idle'] = options['R0']
    send['sos_phone'] = options['G0'] + ',' + options['G1'] + ',' + options['G2'] \
       + ',' + options['G3'] + ',' + options['G4'] + ',' + options['G5']
    send['uid'] = options['B2']

    return send

  def dispatch(self):
    """
     Dispatching data from socket
    """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    data_socket = self.recv().decode()
    log.debug("Data recieved:\n%s", data_socket)

    while len(data_socket) > 0:
      function_name = self.getFunction(data_socket)
      function = getattr(self, function_name)
      function(data_socket)
      data_socket = self.recv().decode()

  def getFunction(self, data):
    """
     Returns a function name according to supplied data
     @param data: data string
     @return: function name
    """
    data_type = data.split(",")[0]

    if data_type == 'OBS':
      return "processRequest"
    elif data_type == 'GSs':
      return "processSettings"
    elif data_type == 'GSr':
      return "processData"
    else:
      raise NotImplementedError("Unknown data type" + data_type)

  def processData(self, data):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
    """
    rc = self.re_compiled['report']
    position = 0

    m = rc.search(data, position)
    if not m:
      self.processError(data)

    while m:
      # - OK. we found it, let's see for checksum
      log.debug("Raw match found.")
      data_device = m.groupdict()
      cs1 = str.upper(data_device['checksum'])
      cs2 = str.upper(self.getChecksum(data_device['line']))
      if (cs1 == cs2):
        data_observ = self.translate(data_device)
        data_observ['__rawdata'] = m.group(0)
        log.info(data_observ)
        self.uid = data_observ['uid']
        store_result = self.store([data_observ])
        if data_observ['sensors']['sos'] == 1:
          self.stopSosSignal()
      else:
        log.error("Incorrect checksum: %s against computed %s", cs1, cs2)
      position += len(m.group(0))
      m = rc.search(data, position)

    return super(GlobalsatHandler, self).processData(data)

  def stopSosSignal(self):
    """
     Send command to stop sos signal
    """
    command = 'GSC,' + self.uid + ',Na'
    command = self.addChecksum(command)
    log.debug('Command sent: ' + command)
    self.send(command.encode())
    return self

  def processSettings(self, data):
    """
     Reading of device settings
     @param data: data string with device settings
     @return: self
    """
    rc = self.re_compiled['search_config']
    position = 0
    m = rc.search(data, position)

    if not m:
      self.processError(data)

    while m:
      log.debug("Config match found.")
      data_settings = m.groupdict()
      self.saveSettings(data_settings)
      position += len(m.group(0))
      m = rc.search(data, position)

    return self

  def saveSettings(self, data):
    """
     Save device setting
     @param data: device setting
    """
    current_db = db.get(data['uid'])
    current_db.addRead(data['data'])
    log.debug('Transmission status: ' + data['status'])
    if data['status'] == '2':
      current_db.endRead()

  def processError(self, data):
    """
     OK. Our pattern doesn't match the socket or config data.
     The source of the problem can be in wrong report format.
     Let's try to find UID of device.
     Later it would be good to load particular config for device by its uid
    """
    rc = self.re_compiled['search_uid']
    mu = rc.search(data)
    if not mu:
      log.error("Unknown data format...")
    else:
      log.error("Unknown data format for %s", mu.group('uid'))

  def processCommandFormat(self, data):
    """
     Processing command to form config string
     @param data: request
    """
    string = self.commandStart.format(data['identifier'])

    if data['options'] == 'DEFAULT':
      options = self.default_options
    else:
      raise NotImplementedError("Custom options not implemented yet")

    string = string + self.parseOptions(options, data)
    string = self.addChecksum(string)
    self.send(string.encode())

  def processCommandRead(self, data):
    """
     Sending command to read all of device configuration
     @param data: data string
    """
    current_db = db.get(self.uid)
    if not current_db.isReading() and not current_db.isReadReady():
      command = 'GSC,' + self.uid + ',L1(ALL)'
      command = self.addChecksum(command)
      log.debug('Command sent: ' + command)
      current_db.startReading()
      self.send(command.encode())

  def processCommandSet(self, data):
    """
     Set device configuration
     @param data: data dict()
    """
    command = 'GSS,' + self.uid + ',3,0,'
    for option, value in data.items():
      if option == 'freq_mov':
        command += 'R1=' + value
      elif option == 'freq_idle':
        command += 'R0=' + value
      elif option == 'sos_phone':
        command += 'H0=03,G0=' + value
      else:
        log.error('Unknown option: ' + data.option)

    command = self.addChecksum(command)
    log.debug('Command sent: ' + command)
    self.send(command.encode())

  def parseOptions(self, options, data):
    """
     Converts options to string
     @param options: options
     @param data: request data
     @return: string
    """
    ret = ',O3=' + str(self.getRawReportFormat())
    for key in options:
      ret += ',' + key + '=' + options[key]

    ret += ',D1=' + str(data['gprs']['apn'])
    ret += ',D2=' + str(data['gprs']['username'])
    ret += ',D3=' + str(data['gprs']['password'])
    ret += ',E0=' + str(data['host'])
    ret += ',E1=' + str(data['port'])

    return ret
