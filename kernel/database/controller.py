# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Database handler class
@copyright 2009-2012, Maprox Ltd.
'''

from kernel.database.abstract import DatabaseAbstract

class DatabaseController(DatabaseAbstract):
    """ key for reading commands """
    _commandKey = 'zc:k:tracker_controller'
    """ param for requesting commands """
    _requestParam = 'controller=1'

    def getLogName(self):
        """ Returns name to write in logs """
        return 'Controller'
