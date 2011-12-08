# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''

import sqlite3
from kernel.config import conf
from kernel.logger import log

class Database(object):
  """ Database handler """
  __db = None
  __cursor = None

  def __init__(self):
    """ Constructor. Creates local database to be used by protocol handlers """
    db = sqlite3.connect('db/' + conf.protocols[0], check_same_thread = False)
    cursor = db.cursor()

    cursor.execute('create table if not exists read (id INTEGER PRIMARY KEY, uid VARCHAR(60), part INTEGER, message TEXT)')
    db.commit()

    self.__db = db
    self.__cursor = cursor

  def get(self):
    """ Returns the database object """
    return self.__cursor

  def commit(self):
    """ Commits changes """
    self.__db.commit()

  def execute(self, string):
    """ Execute statement """
    self.__cursor.execute(string)

  def fetchall(self):
    """ Fetch data """
    return self.__cursor.fetchall()

# let's create instance of global database
db = Database()
