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

  default_options = {
    # SOS Report count
    # 0 = None, 1 = SMS, 2 = TCP, 3 = SMS and TCP, 4 = UDP
    'H0': '3',
    # SOS Max number of SMS report for each phone number
    'H1': '1',
    # SOS Report interval
    'H2': '30',
    # SOS Max number of GPRS report (0=continues until
    # dismissed via GSC,[IMEI],Na*QQ!)
    'H3': '1',
    # Don't wait acknowledgement from server, dont't send one
    'A0': '0',
    'A1': '0',
    # Turn off voice monitoring
    'V0': '0',
    # Asking TR-600 to report by TCP (Qa=02, Qb=02) if ACC status is changed.
    'Qa': '02',
    'Qb': '02',
    # Enable odometer when ACC input is activated (Qc=43).
    'Qc': '43',
    # Disable odometer when ACC input goes inactive (Qd=42)
    'Qd': '42'
  }