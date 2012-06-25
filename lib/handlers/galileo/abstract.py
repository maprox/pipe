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
import lib.handlers.galileo.tags as tags


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

    packnum = 0
    while len(data_socket) > 0:
      self.processData(data_socket, packnum)
      self.sendAcknowledgement()
      data_socket = self.recv()
      packnum += 1

    return super(GalileoHandler, self).dispatch()

  def processData(self, data, packnum):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @param packnum: Number of socket packet
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
    self.__lastdata = data_device

    # now let's read packet tags
    # but before this, check tagsdata length
    tagsdata = buffer[3:-2]
    if len(tagsdata) != length:
      raise Exception('Data length Is incorrect!');

    tagslist = []
    tail = 1
    try:
      while tail < length:
        tagnum = tagsdata[tail - 1]
        taglen = tags.getLengthOfTag(tagnum)
        tagdata = tagsdata[tail : tail + taglen]
        tagslist.append(tags.Tag.getInstance(tagnum, tagdata))
        tail += taglen + 1
    except:
      log.error("Incorrect tag: %s", traceback.format_exc())
      raise Exception('Incorrect tag?')
    data_device['tags'] = tagslist

    packet = self.translate(data_device)
    if (packnum == 0):
      # HeadPack
      self.headpack = packet
      return
    # MainPack
    packet.update(self.headpack)
    log.info(packet)
    store_result = self.store([packet])
    return super(GalileoHandler, self).processData(data)

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    if (data == None): return None

    packet = {}
    packet['sensors'] = {}
    for tag in data['tags']:
      num = tag.getNumber()
      value = tag.getValue()
      #print(num, value)
      if (num == '3'): # IMEI
        packet['uid'] = value
      elif (num == '4'): # CODE
        packet['uid2'] = value
      elif (num == '32'): # Timestamp
        packet['time'] = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
      elif (num == '48'): # Satellites count, Correctness, Latitude, Longitude
        packet.update(value)
      elif (num == '51'): # Speed, Azimuth
        packet.update(value)
      elif (num == '52'): # Altitude
        packet['altitude'] = value
      elif (num == '53'): # HDOP
        packet['hdop'] = value
      elif (num == '64'): # Status
        packet.update(value)
        packet['sensors']['acc'] = value['acc']
        packet['sensors']['sos'] = value['sos']
        packet['sensors']['battery_discharge'] = value['battery_discharge']
      elif (num == '80'): # Analog input 0
        packet['sensors']['analog_input0'] = value
      elif (num == '81'): # Analog input 1
        packet['sensors']['analog_input1'] = value
      elif (num == '82'): # Analog input 2
        packet['sensors']['analog_input2'] = value
      elif (num == '83'): # Analog input 3
        packet['sensors']['analog_input3'] = value

    return packet

  def sendAcknowledgement(self):
    """
     Sends acknowledgement to the socket
    """
    crc = self.__lastdata['crc']
    buf = self.getAckPacket(crc)
    return self.send(buf)

  @classmethod
  def getAckPacket(cls, crc):
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


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

  def setUp(self):
    pass
