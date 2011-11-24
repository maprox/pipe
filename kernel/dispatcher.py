# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Dispatcher of protocols
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/kernel/dispatcher.py $
@version   $Id: dispatcher.py 406 2011-02-28 14:24:53Z sunsay $
'''

from kernel.config import conf
from kernel.logger import log

import kernel.pipe as pipe
from lib.handlers.list import handlersList

class Dispatcher(object):
  """ Protocol dispatcher """
  __store = None

  def __init__(self):
    """ Constructor. Creates local storage to be used by protocol handlers """
    log.debug('%s::__init__()', self.__class__)
    self.__store = pipe.Manager()

  def getStore(self):
    """ Returns the store object """
    return self.__store

  def dispatch(self, clientThread):
    """ Dispatching incoming data from device to protocol handler """
    self.__thread = clientThread
    for HandlerClass in handlersList:
      log.debug('Protocol handler: %s', HandlerClass.__doc__)
      HandlerClass(self.getStore(), clientThread).dispatch()
      return
    log.debug('No protocol handlers found')

# let's create instance of global protocol dispatcher
disp = Dispatcher()
