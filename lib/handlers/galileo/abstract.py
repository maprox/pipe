# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net>
@info      Galileo base class for other Galileo firmware
@copyright 2012, Maprox LLC
'''

import time, datetime
from struct import unpack, pack, calcsize

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.crc16 as crc16
import lib.bits as bits
import lib.handlers.galileo.tags as tags
import lib.handlers.galileo.packets as packets

# ---------------------------------------------------------------------------

class GalileoHandler(AbstractHandler):
  """
   Base handler for Galileo protocol
  """
  __commands = {}
  __commands_num_seq = 0
  __imageRecievingConfig = None

  def dispatch(self):
    """
     Dispatching data from socket
    """
    AbstractHandler.dispatch(self)

    log.debug("Recieving...")
    packnum = 0
    buffer = self.recv()
    while len(buffer) > 0:
      self.processData(buffer)
      if (packnum == 1) and (self.__imageRecievingConfig is None):
        self.sendCommand('Makephoto 1')
      buffer = self.recv()
      packnum += 1

    return super(GalileoHandler, self).dispatch()

  def processData(self, data):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @param packnum: Number of socket packet (defaults to 0)
     @return: self
    """
    protocolPackets = packets.Packet.getPacketsFromBuffer(data)
    for protocolPacket in protocolPackets:
      self.processProtocolPacket(protocolPacket)

    if self.__imageRecievingConfig is None:
      return super(GalileoHandler, self).processData(data)

  def processProtocolPacket(self, protocolPacket):
    """
     Process galileo packet.
     @param protocolPacket: Galileo protocol packet
    """
    observerPackets = self.translate(protocolPacket)
    self.sendAcknowledgement(protocolPacket)

    if (protocolPacket.hasTag(0xE1)):
      log.info('Device answer is "' +
        protocolPacket.getTag(0xE1).getValue() + '".')

    if (len(observerPackets) > 0):
      if 'uid' in observerPackets[0]:
        self.headpack = observerPackets[0]
        self.uid = self.headpack['uid']
        log.info('HeadPack is stored.')
        return

    if (protocolPacket.header == 4):
      return self.recieveImage(protocolPacket)

    log.info('Location packet not found. Exiting...')
    if len(observerPackets) == 0: return

    # MainPack
    for packet in observerPackets:
      packet.update(self.headpack)
    #packet['__packnum'] = packnum
    #packet['__rawdata'] = buffer
    log.info(observerPackets)
    store_result = self.store(observerPackets)

  def sendCommand(self, command):
    """
     Sends command to the tracker
     @param command: Command string
    """
    log.info('Sending "' + command + '"...')
    packet = packets.Packet()
    packet.header = 1
    packet.addTag(0x03, self.headpack['uid'])
    packet.addTag(0x04, self.headpack['uid2'])
    packet.addTag(0xE0, self.__commands_num_seq)
    packet.addTag(0xE1, command)
    self.send(packet.rawdata)
    # save sended command in local dict
    self.__commands[self.__commands_num_seq] = packet
    self.__commands_num_seq += 1 # increase command number sequence

  def recieveImage(self, packet):
    """
     Recieves an image from tracker.
     Sends it to the observer server, when totally recieved.
    """
    if (packet == None) or (packet.body == None) or (len(packet.body) == 0):
      log.error('Empty image packet. Transfer aborted!')
      return

    config = self.__imageRecievingConfig
    partnum = packet.body[0]
    if self.__imageRecievingConfig is None:
      self.__imageRecievingConfig = {
        'imageparts': {}
      }
      config = self.__imageRecievingConfig
      log.info('Image transfer is started.')
    else:
      if len(packet.body) > 1:
        log.debug('Image transfer in progress...')
        log.debug('Size of chunk is %d bytes', len(packet.body) - 1)
      else:
        imagedata = b''
        imageparts = self.__imageRecievingConfig['imageparts']
        for num in sorted(imageparts.keys()):
          imagedata += imageparts[num]
        self.sendImages([{
          'mime': 'image/jpeg',
          'content': imagedata
        }])
        self.__imageRecievingConfig = None
        log.debug('Transfer complete.')
        return

    imagedata = packet.body[1:]
    config['imageparts'][partnum] = imagedata

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    packets = []
    if (data == None): return packets
    if (data.tags == None): return packets

    packet = {'sensors': {}}
    prevNum = 0
    for tag in data.tags:
      num = tag.getNumber()

      if (num < prevNum):
        packets.append(packet)
        packet = {'sensors': {}}

      prevNum = num
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

    packets.append(packet)
    return packets

  def sendAcknowledgement(self, packet):
    """
     Sends acknowledgement to the socket
    """
    buf = self.getAckPacket(packet.crc)
    log.info("Send acknowledgement, crc = %d" % packet.crc)
    return self.send(buf)

  @classmethod
  def getAckPacket(cls, crc):
    """
      Returns acknowledgement buffer value
    """
    return pack('<BH', 2, crc)

  def processCommandExecute(self, data):
    """
     Execute command for the device
     @param data: data dict()
    """
    log.info('Observer is sending a command:')
    log.info(data)
    self.sendCommand(data['command'])

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

  def setUp(self):
    pass

  def test_packetData(self):
    import kernel.pipe as pipe
    h = GalileoHandler(pipe.Manager(), None)
    data = b'\x01"\x00\x03868204000728070\x042\x00\xe0\x00\x00\x00\x00\xe1\x08Photo ok\x137'
    protocolPackets = packets.Packet.getPacketsFromBuffer(data)
    for packet in protocolPackets:
      self.assertEqual(packet.header, 1)