# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat base class for other Globalsat protocols
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL$
@version   $Id$
"""

import re
import json
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handler import AbstractHandler
from lib.geo import Geo

class GlobalsatHandler(AbstractHandler):
  """ Base handler for Globalsat protocol """

  confSectionName = "globalsat.protocolname"
  reportFormat = "SPRXYAB27GHKLMmnaefghio*U!"

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
    'search_uid': 'GS\w,(?P<uid>\w+)',
    'request': '^OBS,device\((?P<data>[^\)]+)\),options\((?P<options>[^\)]+)\)$'
  }

  re_compiled = {
    'service': None,
    'report': None,
    'search_uid': None,
    'request': None
  }

  default_options = {}

  re_volts = re.compile('(\d+)mV')
  re_percents = re.compile('(\d+)%')

  def __init__(self, store, thread):
    """ Constructor """
    AbstractHandler.__init__(self, store, thread)

  @classmethod
  def truncateCheckSum(cls, value):
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
      self.reportFormat = self.truncateCheckSum(section.get(
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
    self.re_compiled['request'] = \
      re.compile(p['request'])
    return self

  def prepare(self):
    """ Preparing for data transfer """
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
        packet['sensors']['speed'] = packet['speed']
      # SPEED (km/hr)
      elif char == "I":
        packet['speed'] = value
        packet['sensors']['speed'] = packet['speed']
      # SPEED (mile/hr)
      elif char == "J":
        packet['speed'] = 1.609344 * float(value)
        packet['sensors']['speed'] = packet['speed']
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
        packet['sensors']['gps_antenna_fail'] = (dec >> 2) % 2
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
      elif char == "n":
        packet['battery_level'] = value
        if (self.re_volts.match(value)):
          packet['battery_level'] = 1
        else:
          if (self.re_percents.match(value)):
            percents = float(self.re_percents.search(value).group(1)) / 100
            packet['battery_level'] = percents
    return packet

  def dispatch(self):
    """ Dispatching data from socket """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    data_socket = self.recv()
    log.debug("Data recieved:\n%s", data_socket)
    function_name = self.getFunction(data_socket)
    function = getattr(self, function_name)

    while len(data_socket) > 0:
      function(data_socket)
      data_socket = self.recv()

  def getFunction(self, data):
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
    rc_uid = self.re_compiled['search_uid']
    position = 0

    m = rc.search(data, position)
    if not m:
      """
       OK. Our pattern doesn't match the socket data.
       The source of the problem can be in wrong report format.
       Let's try to find UID of device.
     - Later it would be good to load particular config for device by its uid
      """
      mu = rc_uid.search(data, position)
      if not mu:
        log.error("Unknown data format...")
      else:
        log.error("Unknown data format for %s", mu.group('uid'))

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
        store_result = self.store([data_observ])
      else:
        log.error("Incorrect checksum: %s against computed %s", cs1, cs2)
      position += len(m.group(0))
      m = rc.search(data, position)

    return self

  def processSettings(self, data):
    raise NotImplementedError("processSettings must be defined in child class")

  def processRequest(self, data):
    """
     Processing of observer request from socket
     @param data: request
    """
    rc = self.re_compiled['request']
    position = 0

    m = rc.search(data, position)
    if m:
      log.debug("Request match found.")
      data = m.groupdict()['data']
      data = json.loads(data)
      options = m.groupdict()['options']

      string = self.commandStart.format(data['identifier'])

      if options == 'DEFAULT':
        options = self.default_options
      else:
        raise NotImplementedError("Custom options not implemented yet")

      string = string + self.parseOptions(options, data)
      string = self.addChecksum(string) + self.transmissionEndSymbol
      self.send(string.encode())

    else:
      log.error("Incorrect request format")

    return self
