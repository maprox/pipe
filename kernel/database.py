# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''
import os.path

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

  def isReading(self):
    """ Tests, if currently in reading state """
    return os.path.exists(self.getPath())

  def startReading(self):
    """ Starts reading """
    path = self.getPath()
    file = open(path, 'w')
    file.write('')
    file.close()

# let's create instance of global database manager
db = DatabaseManager()
