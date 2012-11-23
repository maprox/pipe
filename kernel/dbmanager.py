# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Database handler class
@copyright 2009-2012, Maprox LLC
'''

from kernel.database.controller import DatabaseController
from kernel.database.handler import DatabaseHandler

class DatabaseManager(object):
    """ Database handlers """
    __db = {}
    __dbController = False

    def __init__(self):
        self.__db = {}

    def get(self, uid):
        """ Returns the database object """

        if not uid in self.__db:
            self.__db[uid] = DatabaseHandler(uid)

        return self.__db[uid]

    def getController(self):
        """ Returns the database object for controller """

        if not self.__dbController:
            self.__dbController = DatabaseController()

        return self.__dbController

# let's create instance of global database manager
db = DatabaseManager()
