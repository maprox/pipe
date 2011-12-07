# -*- coding: utf8 -*-
"""
@project   Maprox Observer <http://maprox.net/observer>
@info      Globalsat TR-206
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL$
@version   $Id$
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
