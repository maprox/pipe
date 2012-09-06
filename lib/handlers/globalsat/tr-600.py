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
    if 'O5' in options:
      send['identifier'] = options['O5']
    if 'O7' in options:
      send['version'] = options['O7']
    if 'Ri' in options:
      send['freq_mov'] = options['Ri']
    if 'Ra' in options:
      send['freq_idle'] = options['Ra']
    if 'Ro' in options:
      send['send_mov'] = options['Ro']
    if 'G0' in options:
      send['sos_phone_1'] = options['G0']
    if 'G1' in options:
      send['sos_phone_2'] = options['G1']
    if 'G2' in options:
      send['sos_phone_3'] = options['G2']
    if 'G3' in options:
      send['sos_phone_4'] = options['G3']
    if 'G4' in options:
      send['sos_phone_5'] = options['G4']
    if 'G5' in options:
      send['sos_phone_6'] = options['G5']
    if 'V4' in options:
      send['voice_phone_1'] = options['V4']
    if 'V8' in options:
      send['voice_phone_2'] = options['V8']
    if 'V9' in options:
      send['voice_phone_3'] = options['V9']
    if 'V0' in options:
      send['voice_call_on_sos'] = options['V0']

    return send

  def addCommandSetOptions(self, data):
    """
     Add device options
     @param data: data dict()
    """
    command = GlobalsatHandler.addCommandSetOptions(self, data)
    for item in data:
      if item['option'] == 'freq_mov':
        command += ',Ri=' + item['value']
      elif item['option'] == 'freq_idle':
        command += ',Ra=' + item['value']
      elif item['option'] == 'send_mov':
        command += ',Ro=' + item['value']
      elif item['option'] == 'sos_phone_1':
        command += ',G0=' + item['value']
      elif item['option'] == 'sos_phone_2':
        command += ',G1=' + item['value']
      elif item['option'] == 'sos_phone_3':
        command += ',G2=' + item['value']
      elif item['option'] == 'sos_phone_4':
        command += ',G3=' + item['value']
      elif item['option'] == 'sos_phone_5':
        command += ',G4=' + item['value']
      elif item['option'] == 'sos_phone_6':
        command += ',G5=' + item['value']
      elif item['option'] == 'voice_phone_1':
        command += ',V4=' + item['value']
      elif item['option'] == 'voice_phone_2':
        command += ',V8=' + item['value']
      elif item['option'] == 'voice_phone_3':
        command += ',V9=' + item['value']
      elif item['option'] == 'voice_call_on_sos':
        command += ',V0=' + item['value']
    return command
