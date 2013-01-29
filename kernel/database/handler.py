# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Database handler class
@copyright 2009-2013, Maprox LLC
'''

import time
from kernel.database.abstract import DatabaseAbstract

class DatabaseHandler(DatabaseAbstract):
    """ uid storage """
    _uid = None

    def __init__(self, uid):
        """
         Constructor. Sets uid
         @param uid: Device IMEI
        """
        self._uid = uid
        self._commandKey = 'zc:k:tracker_action' + uid
        self._requestParam = 'uid=' + self._uid
        DatabaseAbstract.__init__(self)

    def set(self, key, value):
        """
         Adds data for specified key
         @param key: string
         @param value:
        """
        self._store.hset(self._settingsKey(), key, value)

    def get(self, key):
        """
         Returns value from storage by key
         @param key: string
         @return: value
        """
        current = self._store.hget(self._settingsKey(), key)
        if current is None:
            current = b''
        return current

    def has(self, key):
        """
         Returns True if key exists in storage
         @param key: string
         @return: bool
        """
        return self._store.hexists(self._settingsKey(), key)

    def remove(self, key):
        """
         Removes key from storage
         @param key: string
        """
        return self._store.hdel(self._settingsKey(), key)

    def getLogName(self):
        """ Returns name to write in logs """
        return 'uid ' + self._uid

    def isReadingSettings(self):
        """ Tests, if currently in reading state """
        return self.has('reading') \
            and float(self.get('start')) + 600 > time.time()

    def isSettingsReady(self):
        """ Tests, if currently have ready read """
        return self.has('data') and not self.has('reading')

    def startReadingSettings(self, task):
        """
         Starts reading
         @param task: id task
        """
        self.set('task', task)
        self.set('reading', 1)
        self.set('start', time.time())

    def finishSettingsRead(self):
        """ Marks data as ready """
        self.remove('reading')

    def addSettings(self, string):
        """ Adds string reading """
        return self.set('data', self.getSettings() + string)

    def getSettings(self):
        """ return ready data """
        return self.get('data').decode()

    def getSettingsTaskId(self):
        """ return ready data """
        return self.get('task')

    def deleteSettings(self):
        """ Deletes data """
        self._store.delete(self._settingsKey())

    def _settingsKey(self):
        return 'tracker_setting' + self._uid
