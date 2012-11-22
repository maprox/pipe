# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset base class for other Naviset firmware
@copyright 2012, Maprox LLC
'''

import time, datetime
from struct import unpack, pack, calcsize

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.crc16 as crc16
import lib.bits as bits
#import lib.handlers.galileo.tags as tags
import lib.handlers.naviset.packets as packets

# ---------------------------------------------------------------------------

class NavisetHandler(AbstractHandler):
  """
   Base handler for Naviset protocol
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
    buffer = self.recv()
    while len(buffer) > 0:
      self.processData(buffer)
      buffer = self.recv()

    return super(NavisetHandler, self).dispatch()

  def processData(self, data):
    """
     Processing of data from socket / storage.
     @param data: Data from socket
     @param packnum: Number of socket packet (defaults to 0)
     @return: self
    """
    if (len(data) >= 3) and (data[:3] == b'OBS'):
      return self.processRequest(data.decode())

    protocolPackets = packets.PacketFactory.getPacketsFromBuffer(data)
    for protocolPacket in protocolPackets:
      self.processProtocolPacket(protocolPacket)

    return super(NavisetHandler, self).processData(data)

  def processProtocolPacket(self, protocolPacket):
    """
     Process naviset packet.
     @param protocolPacket: Naviset protocol packet
    """
    self.sendAcknowledgement(protocolPacket)
    if isinstance(protocolPacket, packets.PacketHead):
      log.info('HeadPack is stored.')
      self.uid = protocolPacket.deviceIMEI
      return

    observerPackets = self.translate(protocolPacket)
    if len(observerPackets) == 0:
      log.info('Location packet not found. Exiting...')
      return

    log.info(observerPackets)
    store_result = self.store(observerPackets)

  def sendCommand(self, command):
    """
     Sends command to the tracker
     @param command: Command string
    """
    log.info('Sending "' + command + '"...')
    log.info('[IS NOT IMPLEMENTED]')

  def receiveImage(self, packet):
    """
     Receives an image from tracker.
     Sends it to the observer server, when totally received.
    """
    log.error('Image receiving...')
    log.info('[IS NOT IMPLEMENTED]')

  def translate(self, protocolPacket):
    """
     Translate gps-tracker data to observer pipe format
     @param protocolPacket: Naviset protocol packet
    """
    list = []
    if (protocolPacket == None): return list
    if not isinstance(protocolPacket, packets.PacketData):
        return list
    if (len(protocolPacket.items) == 0):
        return list
    for item in protocolPacket.items:
        packet = {'uid': self.uid}
        packet.update(item.params)
        packet['time'] = packet['time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
        list.append(packet)
        #packet['sensors']['acc'] = value['acc']
        #packet['sensors']['sos'] = value['sos']
        #packet['sensors']['extbattery_low'] = value['extbattery_low']
        #packet['sensors']['analog_input0'] = value
    return list

  def sendAcknowledgement(self, packet):
    """
     Sends acknowledgement to the socket
     @param packet: a L{packets.Packet} subclass
    """
    buf = self.getAckPacket(packet)
    log.info("Send acknowledgement, crc = %d" % packet.crc)
    return self.send(buf)

  @classmethod
  def getAckPacket(cls, packet):
    """
     Returns acknowledgement buffer value
     @param packet: a L{packets.Packet} subclass
    """
    return b'\x01' + pack('<H', packet.crc)

  def processCommandExecute(self, task, data):
    """
     Execute command for the device
     @param task: id task
     @param data: data dict()
    """
    log.info('Observer is sending a command:')
    log.info(data)
    self.sendCommand(data['command'])

  def processCommandFormat(self, task, data):
    """
     Processing command to form config string
     @param task: id task
     @param data: request
    """
    pass

  def processCommandReadSettings(self, task, data):
    """
     Sending command to read all of device configuration
     @param task: id task
     @param data: data string
    """
    pass

  def processCommandSetOption(self, task, data):
    """
     Set device configuration
     @param task: id task
     @param data: data dict()
    """
    pass

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
    h = NavisetHandler(pipe.Manager(), None)
    #data = b'\x01"\x00\x03868204000728070\x042\x00\xe0\x00\x00\x00\x00\xe1\x08Photo ok\x137'
    #protocolPackets = packets.PacketFactory.getPacketsFromBuffer(data)
    protocolPackets = []
    for packet in protocolPackets:
      self.assertEqual(packet.header, 1)
