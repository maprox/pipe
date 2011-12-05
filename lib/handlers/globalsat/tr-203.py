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
    'H3': '1'
  }

  def parseOptions(self, options, data):
    """
     Converts options to string
     @param options: options
     @param data: request data
    """

    ret = ',O3=' + str(self.getRawReportFormat())
    for key in options:
      ret += ',' + key + '=' + options[key]

    ret += ',D1=' + str(data['gprs']['apn'])
    ret += ',D2=' + str(data['gprs']['username'])
    ret += ',D3=' + str(data['gprs']['password'])
    ret += ',E0=' + str(data['host'])
    ret += ',E1=' + str(data['port'])

    return ret
