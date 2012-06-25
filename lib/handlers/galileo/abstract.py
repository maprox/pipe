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
from struct import unpack, pack, calcsize
from lib.handler import AbstractHandler
from lib.geo import Geo
import lib.crc16 as crc16
import lib.bits as bits


class GalileoHandler(AbstractHandler):
  """
   Base handler for Galileo protocol
  """

  # last parsed data from tracker
  __lastdata = None

  def dispatch(self):
    """
     Dispatching data from socket
    """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    data_socket = self.recv()
    log.debug("Data recieved:\n%s", data_socket)

    while len(data_socket) > 0:
      self.processData(data_socket)
      self.sendAcknowledgement()
      data_socket = self.recv()

    return super(GalileoHandler, self).processData(data)

  def processData(self, data):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @return: self
    """
    # Parse data assuming that it is a galileo Packet
    # first of all check crc of supplied data
    buffer = data
    crc = unpack("<H", buffer[-2:])[0]
    crc_data = buffer[:-2]
    if not self.isCorrectCrc(crc_data, crc):
       raise Exception('Crc Is incorrect!');

    # read header and length
    header, length = unpack("<BH", buffer[:3])
    hasArchive = bits.bitTest(length, 15)
    length = bits.bitClear(length, 15)

    data_device = {}
    data_device['header'] = header
    data_device['length'] = length
    data_device['hasarchive'] = hasArchive
    data_device['crc'] = crc

    # now let's read packet tags
    # but before this, check tagsdata length
    tagsdata = buffer[3:-2]
    if len(tagsdata) != length:
      raise Exception('Data length Is incorrect!');

    tagslist = {}
    tail = 1
    try:
      while tail < length:
        tagnum = tagsdata[tail - 1]
        taglen = tags.getLengthOfTag(tagnum)
        tagdata = tagsdata[tail : tail + taglen]
        tagslist[tagnum] = tags.Tag.getInstance(tagnum, tagdata)
        tail += taglen + 1
    except:
      raise Exception('Incorrect tag?')
    data_device['tags'] = tagslist

    data_observ = self.translate(data_device)
    log.info(data_observ)
    #self.uid = data_observ['uid']
    store_result = self.store([data_observ])
    #if data_observ['sensors']['sos'] == 1:
    #  self.stopSosSignal()
    self.__lastdata = data_device
    return super(GalileoHandler, self).processData(data)

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    packet = {}
    packet['sensors'] = {}
    # TODO
    return packet

  def sendAcknowledgement(self):
    """
     Sends acknowledgement to the socket
    """
    crc = self.__lastdata['crc']
    buf = self.getAckPacket(crc)
    return self.send(buf)

  @classmethod
  def getAckPack(cls, crc):
    """
      Returns acknowledgement buffer value
    """
    return pack('<BH', 2, crc)

  @classmethod
  def isCorrectCrc(cls, buffer, crc):
    """
     Checks buffer CRC (CRC-16 Modbus)
     @param buffer: binary string
     @param crc: binary string
     @return: True if buffer crc equals to supplied crc value, else False
    """
    crc_calculated = crc16.Crc16.calcBinaryString(
      buffer, crc16.INITIAL_MODBUS)
    return crc == crc_calculated
