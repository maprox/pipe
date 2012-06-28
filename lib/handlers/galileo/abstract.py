# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net>
@info      Galileo base class for other Galileo firmware
@copyright 2012, Maprox LLC
'''

import traceback
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
import lib.handlers.galileo.packets as packets

# ---------------------------------------------------------------------------

class GalileoHandler(AbstractHandler):
  """
   Base handler for Galileo protocol
  """

  # last parsed packet from tracker
  __lastDataPacket = None

  def dispatch(self):
    """
     Dispatching data from socket
    """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    packnum = 0
    buffer = self.recv()
    while len(buffer) > 0:
      self.processData(buffer, packnum)
      self.sendAcknowledgement()
      if packnum == 1:
        self.sendCommand()
      buffer = self.recv()
      packnum += 1

    return super(GalileoHandler, self).dispatch()

  def sendCommand(self):
    log.info('Sending command...')
    packet = packets.Packet()
    packet.header = 1
    tagslist = []
    tagslist.append(tags.Tag.getInstance(0x03, self.headpack['uid']))
    tagslist.append(tags.Tag.getInstance(0x04, self.headpack['uid2']))
    tagslist.append(tags.Tag.getInstance(0xE0, 1))
    tagslist.append(tags.Tag.getInstance(0xE1, 'Makephoto 1'))
    packet.tags = tagslist
    self.send(packet.rawdata)

  def processData(self, data, packnum = 0):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @param packnum: Number of socket packet (defaults to 0)
     @return: self
    """
    galileoPacket = packets.Packet(data)
    self.__lastDataPacket = galileoPacket

    if (galileoPacket.header == 4):
      log.info('HEADER 4 !!!')
      with open("/tmp/photo.jpg", "ab") as photo:
        photo.write(galileoPacket.body)
      return

    packet = self.translate(galileoPacket)
    if (packnum == 0):
      # HeadPack
      self.headpack = packet
      return

    # MainPack
    packet.update(self.headpack)
    #packet['__packnum'] = packnum
    #packet['__rawdata'] = buffer
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
    for tag in data.tags:
      num = tag.getNumber()
      value = tag.getValue()
      #print(num, value)
      if (num == 3): # IMEI
        packet['uid'] = value
      elif (num == 4): # CODE
        packet['uid2'] = value
      elif (num == 32): # Timestamp
        packet['time'] = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
      elif (num == 48): # Satellites count, Correctness, Latitude, Longitude
        packet.update(value)
      elif (num == 51): # Speed, Azimuth
        packet.update(value)
      elif (num == 52): # Altitude
        packet['altitude'] = value
      elif (num == 53): # HDOP
        packet['hdop'] = value
      elif (num == 64): # Status
        packet.update(value)
        packet['sensors']['acc'] = value['acc']
        packet['sensors']['sos'] = value['sos']
        packet['sensors']['battery_discharge'] = value['battery_discharge']
      elif (num == 80): # Analog input 0
        packet['sensors']['analog_input0'] = value
      elif (num == 81): # Analog input 1
        packet['sensors']['analog_input1'] = value
      elif (num == 82): # Analog input 2
        packet['sensors']['analog_input2'] = value
      elif (num == 83): # Analog input 3
        packet['sensors']['analog_input3'] = value

    return packet

  def sendAcknowledgement(self):
    """
     Sends acknowledgement to the socket
    """
    crc = self.__lastDataPacket.crc
    buf = self.getAckPacket(crc)
    log.info("Send acknowledgement, crc = %d" % crc)
    return self.send(buf)

  @classmethod
  def getAckPacket(cls, crc):
    """
      Returns acknowledgement buffer value
    """
    return pack('<BH', 2, crc)

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

  def setUp(self):
    pass
