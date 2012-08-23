# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat TR-203
@copyright 2009-2012, Maprox LLC
"""

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handlers.globalsat.abstract import GlobalsatHandler

class Handler(GlobalsatHandler):
  """ Globalsat. TR-203 """

  confSectionName = "globalsat.tr-203"
  reportFormat = "SPRAB27GHKLMNO*U!"

  def __init__(self, store, thread):
    """ Constructor """
    GlobalsatHandler.__init__(self, store, thread)

    """ Options for Globalsat TR-203 """
    self.default_options.update({
      # 0~65535
      # SMS  0 or 1  = 1 SOS alarm report;
      #      2~65535 = 2~65535 SOS alarm report
      # GPRS 0       = 1 SOS alarm report;
      #      1~65535 = continue send SOS alarm report till receive stop command
      'H1': '0'
    })

  def translateConfigOptions(self, send, options):
    """
     Translate gps-tracker parsed options to observer format
     @param send: {string[]} data to send
     @param options: {string[]} parsed options
    """
    send = GlobalsatHandler.translateConfigOptions(self, send, options)
    if 'R1' in options:
      send['freq_mov'] = options['R1']
    if 'R0' in options:
      send['freq_idle'] = options['R0']

    return send

  def addCommandSetOptions(self, data):
    """
     Add device options
     @param data: data dict()
    """
    command = GlobalsatHandler.addCommandSetOptions(self, data)
    for option, value in data.items():
      if option == 'freq_mov':
        command += ',R1=' + value
      elif option == 'freq_idle':
        command += ',R0=' + value
    return command
