# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat TR-600
@copyright 2009-2012, Maprox LLC
"""

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handlers.globalsat.abstract import GlobalsatHandler

class Handler(GlobalsatHandler):
  """ Globalsat. TR-600 """

  confSectionName = "globalsat.tr-600"
  reportFormat = "SPRXYAB27GHKLMmnaefghio*U!"

  def translateConfigOptions(self, send, options):
    """
     Translate gps-tracker parsed options to observer format
     @param send: {string[]} data to send
     @param options: {string[]} parsed options
    """
    send = GlobalsatHandler.translateConfigOptions(self, send, options)
    if 'Ri' in options:
      send['freq_mov'] = options['Ri']
    if 'Ra' in options:
      send['freq_idle'] = options['Ra']
    if 'Ro' in options:
      send['send_mov'] = options['Ro']
    if 'V4' in options:
      send['voice_phone_1'] = options['V4']
    if 'V8' in options:
      send['voice_phone_2'] = options['V8']
    if 'V9' in options:
      send['voice_phone_3'] = options['V9']
    if 'V0' in options:
      send['voice_call_on_sos'] = options['V0']

    return send

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    packet = GlobalsatHandler.translate(self, data)
    for char in data:
      value = data[char]
      if char == "n":
        packet['batterylevel'] = self.formatBatteryLevel(value)
    return packet

  def addCommandSetOptions(self, data):
    """
     Add device options
     @param data: data dict()
    """
    command = GlobalsatHandler.addCommandSetOptions(self, data)
    for item in data:
      val = str(item['value'])
      if item['option'] == 'freq_mov':
        command += ',Ri=' + val
      elif item['option'] == 'freq_idle':
        command += ',Ra=' + val
      elif item['option'] == 'send_mov':
        command += ',Ro=' + val
      elif item['option'] == 'voice_phone_1':
        command += ',V4=' + val
      elif item['option'] == 'voice_phone_2':
        command += ',V8=' + val
      elif item['option'] == 'voice_phone_3':
        command += ',V9=' + val
      elif item['option'] == 'voice_call_on_sos':
        command += ',V0=' + val
    return command
