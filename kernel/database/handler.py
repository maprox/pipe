# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''

import time
from kernel.database.abstract import DatabaseAbstract

class DatabaseHandler(DatabaseAbstract):
  """ uid storage """
  _uid = None

  def __init__(self, uid):
    """ Constructor. Sets uid """
    self._uid = uid
    self._commandKey = 'zc:k:tracker_action' + uid
    self._requestParam = 'uid=' + self._uid
    DatabaseAbstract.__init__(self)

  def getLogName(self):
    """ Returns name to write in logs """
    return 'uid ' + self._uid

  def isReadingSettings(self):
    """ Tests, if currently in reading state """
    return self._store.hexists(self._settingsKey(), 'reading') \
      and float(self._store.hget(self._settingsKey(), 'start')) + 600 > time.time()

  def isSettingsReady(self):
    """ Tests, if currently have ready read """
    return self._store.hexists(self._settingsKey(), 'data') \
      and not self._store.hexists(self._settingsKey(), 'reading')

  def startReadingSettings(self, task):
    """ Starts reading """
    """ @param task: id task """
    self._store.hset(self._settingsKey(), 'task', task)
    self._store.hset(self._settingsKey(), 'reading', 1)
    self._store.hset(self._settingsKey(), 'start', time.time())

  def finishSettingsRead(self):
    """ Marks data as ready """
    self._store.hdel(self._settingsKey(), 'reading')

  def addSettings(self, string):
    """ Adds string reading """
    self._store.hset(self._settingsKey(), 'data', self.getSettings() + string)

  def getSettings(self):
    """ return ready data """
    current = self._store.hget(self._settingsKey(), 'data')
    if current is None:
      current = ''
    else:
      current = current.decode('utf-8')
    return current

  def getSettingsTaskId(self):
    """ return ready data """
    return self._store.hget(self._settingsKey(), 'task')

  def deleteSettings(self):
    """ Deletes data """
    self._store.delete(self._settingsKey())

  def _settingsKey(self):
    return 'tracker_setting' + self._uid
