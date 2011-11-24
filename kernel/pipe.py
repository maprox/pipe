# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Class implements communication with pipe-controller
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL$
@version   $Id$
'''

from kernel.logger import log
from kernel.config import conf
from kernel.store import Store

import json
from urllib.parse import urlencode
from urllib.request import urlopen

import lib.falcon

class Manager(Store):
  """ Class implements communication with pipe-controller """

  def send(self, obj):
    """ Sending data to the controller receiving packets from the devices """
    result = lib.falcon.FalconAnswer()
    try:
      packets = list()
      if (isinstance(obj, list)):
        # if multiple packets
        packets = obj
      elif (isinstance(obj, dict)):
        # if one packet
        packets.append(obj)
      else:
        return answer
      # Let's create url_data object
      url_data = {'data' : json.dumps({
        'key': conf.pipeKey,
        'packets': packets
      })}
      # Connecting with the server and getting data
      connection = urlopen(conf.pipeSetUrl + urlencode(url_data))
      answer_str = connection.read()
      log.debug(answer_str)
      answer_dec = json.loads(answer_str.decode())
      result.load(answer_dec)
    except Exception as E:
      result.error('500', ['Error sending packets: ' + str(E)])
      log.error(E)
    return result