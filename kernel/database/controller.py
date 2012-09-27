# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Database handler class
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
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
