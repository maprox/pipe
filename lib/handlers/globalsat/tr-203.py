# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat TR-206
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
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
