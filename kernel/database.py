# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''
import os
import time

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

  def __init__(self, uid):
    """ Constructor. Sets uid """
    self.__uid = uid

  def getPath(self):
    """ Returns path to working file """
    return 'db/' + self.__uid

  def getPathReady(self):
    """ Returns path to ready file """
    return 'db/' + self.__uid + '.ready'

  def isReading(self):
    """ Tests, if currently in reading state """
    path = self.getPath()
    if not os.path.exists(path):
      return False

    if os.path.getmtime(path) - time.time() > 86400:
      return False

    return True

  def isReadReady(self):
    """ Tests, if currently have ready read """
    return os.path.exists(self.getPathReady())

  def startReading(self):
    """ Starts reading """
    self.addRead('')

  def addRead(self, string):
    """ Adds string reading """
    path = self.getPath()
    file = open(path, 'w')
    file.write(string + '\n')
    file.close()

  def endRead(self):
    """ Marks data as ready """
    os.rename(self.getPath(), self.getPathReady())

  def getRead(self):
    """ return ready data """
    path = self.getPathReady()
    file = open(path, 'r')
    text = file.read()
    file.close()

    log.info('Reading settings from ' + self.__uid + ': ' + text)

    return text

  def deleteRead(self):
    """ Deletes data """
    os.remove(self.getPath())
    os.remove(self.getPathReady())

# let's create instance of global database manager
db = DatabaseManager()
