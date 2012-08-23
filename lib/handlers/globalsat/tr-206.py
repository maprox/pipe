# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat TR-206
@copyright 2009-2012, Maprox LLC
"""

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handlers.globalsat.abstract import GlobalsatHandler

class Handler(GlobalsatHandler):
  """ Globalsat. TR-206 """

  confSectionName = "globalsat.tr-206"
  reportFormat = "SPRAB27GHKLMNO*U!"

  def translateConfigOptions(self, send, options):
    """
     Translate gps-tracker parsed options to observer format
     @param send: {string[]} data to send
     @param options: {string[]} parsed options
    """
    send = GlobalsatHandler.translateConfigOptions(self, send, options)
    send['freq_mov'] = options['R1']
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
