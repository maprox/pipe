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