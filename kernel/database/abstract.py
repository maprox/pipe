# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''

import json
import redis
from urllib.request import urlopen
from kernel.config import conf
from kernel.logger import log

class DatabaseAbstract(object):
  """ key for reading commands """
  _commandKey = None
  """ param for requesting commands """
  _requestParam = None
  """ Store connection """
  _store = None

  def __init__(self, uid):
    """ Constructor. Inits redis connection """
    if conf.redisPassword:
      self._store = redis.StrictRedis(password=conf.redisPassword, \
        host=conf.redisHost, port=conf.redisPort, db=0)
    else:
      self._store = redis.StrictRedis(host=conf.redisHost, \
        port=conf.redisPort, db=0)

  def getCommands(self):
    log.debug('Redis key is: ' + self._commandKey)
    commands = self._store.hget(self._commandKey, 'd')

    if commands is None:
      connection = urlopen(conf.pipeRequestUrl + self._requestParam)
      commands = self._store.hget(self._commandKey, 'd')

    if commands is None:
      log.error('Error reading actions for uid ' + self._uid)
      commands = '[]'
    else:
      commands = commands.decode("utf-8")

    log.debug('Commands for uid ' + self._uid + ' are: ' + commands)
    return json.loads(commands)
