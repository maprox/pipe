# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Dispatcher of protocol handlers
@copyright 2009-2011, Maprox LLC
'''

from kernel.config import conf
from kernel.logger import log

import kernel.pipe as pipe
from lib.handlers.list import HandlerClass

class Dispatcher(object):
    """
     Protocol dispatcher
    """
    __store = None

    def __init__(self):
        """
         Constructor. Creates local storage to be used by protocol handlers
        """
        log.debug('%s::__init__()', self.__class__)
        self.__store = pipe.Manager()

    def getStore(self):
        """
         Returns the store object
        """
        return self.__store

    def dispatch(self, clientThread):
        """
         Dispatching incoming data from device to protocol handler
        """
        self.__thread = clientThread
        if HandlerClass:
            log.debug('Protocol handler: %s', HandlerClass.__doc__)
            HandlerClass(self.getStore(), clientThread).dispatch()
        else:
            log.error('No protocol handlers found!')
        return self # We are working with first handler only

# let's create instance of global protocol dispatcher
disp = Dispatcher()
