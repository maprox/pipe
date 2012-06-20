# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net>
@info      Galileo base class for other Galileo firmware
@copyright 2012, Maprox LLC
"""

import re
import json
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from kernel.database import db
from lib.handler import AbstractHandler
from lib.geo import Geo
from lib.crc16 import Crc16

class GalileoHandler(AbstractHandler):
  """
   Base handler for Galileo protocol
  """

  def __init__(self, store, thread):
    """
     Constructor
    """
    AbstractHandler.__init__(self, store, thread)

    """ Options for Galileo """
    self.default_options.update({
      # ...
    })

  @classmethod
  def truncateCheckSum(cls, value):
    """
     Truncates checksum part from value string
     @param value: value byte string
     @return: truncated byte string without checksum part
    """
    return value

  @classmethod
  def getChecksum(cls, data):
    """
     Returns the data checksum
     @param data: data byte string
     @return: byte string checksum
    """
    return Crc16.calcByte(data, INITIAL_MODBUS)

  @classmethod
  def addChecksum(cls, data, fmt = "{d}*{c}!"):
    """
     Adds checksum to a data string
     @param data: data string
     @return: data, containing checksum part
    """
    return str.format(fmt, d = data, c = cls.getChecksum(data))

  def prepare(self):
    """ Preparing for data transfer """
    return self

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    packet = {}
    packet['sensors'] = {}
    # TODO
    return packet

  def translateConfig(self, data):
    """
     Translate gps-tracker config data to observer format
     @param data: {string[]} data from gps-tracker
    """
    send = {}
    # TODO
    return send

  def dispatch(self):
    """
     Dispatching data from socket
    """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    data_socket = self.recv()
    log.debug("Data recieved:\n%s", data_socket)

    while len(data_socket) > 0:
      function_name = self.getFunction(data_socket)
      function = getattr(self, function_name)
      function(data_socket)
      data_socket = self.recv()

    return super(GalileoHandler, self).processData(data)

  def getFunction(self, data):
    """
     Returns a function name according to supplied data
     @param data: data byte string
     @return: string (function name)
    """
    if true:
      return "processData"
    else:
      raise NotImplementedError("Unknown data type" + data_type)

  def processData(self, data):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @return: self
    """
    return self