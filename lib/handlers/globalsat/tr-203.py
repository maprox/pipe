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

  default_options = {
    # SOS Report count
    # 0 = None, 1 = SMS, 2 = TCP, 3 = SMS and TCP, 4 = UDP
    'H0': '3',
    # 0~65535
    # SMS  0 or 1  = 1 SOS alarm report;
    #      2~65535 = 2~65535 SOS alarm report
    # GPRS 0       = 1 SOS alarm report;
    #      1~65535 = continue send SOS alarm report till receive stop command
    'H1': '0',
    # Don't wait acknowledgement from server, dont't send one
    'A0': '0',
    'A1': '0',
    # Turn off voice monitoring
    'V0': '0'
  }

