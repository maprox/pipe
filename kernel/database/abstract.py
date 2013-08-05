# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Database handler class
@copyright 2009-2013, Maprox LLC
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

    def __init__(self):
        """ Constructor. Inits redis connection """
        if conf.redisPassword:
            self._store = redis.StrictRedis(password=conf.redisPassword,
                host=conf.redisHost, port=conf.redisPort, db=0)
        else:
            self._store = redis.StrictRedis(host=conf.redisHost,
                port=conf.redisPort, db=0)

    def getLogName(self):
        """ Returns name to write in logs """
        return 'ERROR: Abstract database called directly'
