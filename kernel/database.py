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

class DatabaseManager(object):
  """ Database handlers """
  __db = {}

  def __init__(self):
    self.__db = {}

  def get(self, uid):
    """ Returns the database object """

    if not uid in self.__db:
      self.__db[uid] = Database(uid)

    return self.__db[uid]

class Database(object):
  """ uid storage """
  __uid = None
  __store = None

  def __init__(self, uid):
    """ Constructor. Sets uid """
    self.__uid = uid
    self.__store = redis.StrictRedis(host=conf.redisHost, port=conf.redisPort, db=0)

  def isReadingSettings(self):
    """ Tests, if currently in reading state """
    return self.__store.hexists(self._settingsKey(), 'reading')

  def isSettingsReady(self):
    """ Tests, if currently have ready read """
    return self.__store.hexists(self._settingsKey(), 'data') \
      and !self.__store.hexists(self._settingsKey(), 'reading')

  def startReadingSettings(self):
    """ Starts reading """
    self.__store.hset(self._settingsKey(), 'reading', 1)

  def finishSettingsRead(self):
    """ Marks data as ready """
    self.__store.hdel(self._settingsKey(), 'reading')

  def addSettings(self, string):
    """ Adds string reading """
    current = self.__store.hget(self._settingsKey(), 'data')
    if current is None:
      current = ''
    self.__store.hset(self._settingsKey(), 'data', current + string)

  def getSettings(self):
    """ return ready data """
    return self.__store.hget(self._settingsKey(), 'data')

  def deleteSettings(self):
    """ Deletes data """
    self.__store.delete(self._settingsKey())

  def _settingsKey(self):
    return 'tracker_setting' + self.__uid

  def getCommands(self):
    log.debug('Redis key is: ' + 'zc:k:tracker_action' + self.__uid)
    commands = self.__store.hget('zc:k:tracker_action' + self.__uid, 'd')

    if commands is None:
      connection = urlopen(conf.pipeRequestUrl + 'uid=' + self.__uid)
      commands = self.__store.hget('zc:k:tracker_action' + self.__uid, 'd')

    if commands is None:
      log.error('Error reading actions for uid ' + self.__uid)
      commands = '[]'
    else:
      commands = commands.decode("utf-8")

    log.debug('Commands for uid ' + self.__uid + ' are: ' + commands)
    return json.loads(commands)

# let's create instance of global database manager
db = DatabaseManager()
