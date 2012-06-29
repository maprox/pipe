# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Class implements communication with pipe-controller
@copyright 2009-2011, Maprox LLC
'''

from kernel.logger import log
from kernel.config import conf
from kernel.store import Store

import json
import urllib.parse
import urllib.request

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
      params = urllib.parse.urlencode(url_data).encode('utf-8')
      request = urllib.request.Request(conf.pipeSetUrl)
      request.add_header("Content-Type",
        "application/x-www-form-urlencoded;charset=utf-8")
      connection = urllib.request.urlopen(request, params)
      answer_str = connection.read()
      log.debug(answer_str)
      answer_dec = json.loads(answer_str.decode())
      result.load(answer_dec)
    except Exception as E:
      result.error('500', ['Error sending packets: ' + str(E)])
      log.error(E)
    return result