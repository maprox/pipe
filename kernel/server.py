# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      TCP-server
@copyright 2009-2013, Maprox LLC
'''

import traceback
from threading import Thread
from socketserver import TCPServer
from socketserver import ThreadingMixIn
from socketserver import BaseRequestHandler

from kernel.logger import log
from kernel.config import conf
import kernel.pipe as pipe
from lib.handlers.list import HandlerClass

# ===========================================================================
class ClientThread(BaseRequestHandler):
    """
     RequestHandler's descendant class for our server.
     An object of this class is created for each connection to the server.
     We override the "handle" method and communicate with the client in it.
    """
    __handler = None

    def setup(self):
        pass

    def handle(self):
        try:
            if HandlerClass:
                log.debug('Protocol handler: %s', HandlerClass.__doc__)
                self.__handler = HandlerClass(pipe.Manager(), self)
                self.__handler.dispatch()
            else:
                log.error('No protocol handlers found!')
        except Exception as E:
            log.error("Dispatch error: %s", traceback.format_exc())

    def finish(self):
        log.debug('ClientThread finish')
        if self.__handler:
            log.debug('Delete handler: %s', self.__handler.__class__)
            del self.__handler

# ===========================================================================
class ThreadingServer(ThreadingMixIn, TCPServer):
    """
     Base class for tcp-server multithreading
    """
    allow_reuse_address = True

# ===========================================================================
class Server():
    """
     Multithreaded TCP-server
    """

    def __init__(self, port = 30003):
        """
         Server class constructor
         @param port: Listening port. Optional, default is 30003.
        """
        log.debug("Server::__init__(%s)", port)
        self.host = ""
        self.port = port
        self.server = ThreadingServer((self.host, self.port), ClientThread)

    def run(self):
        """
         Method wich starts TCP-server
        """
        log.debug("Server::run()")
        self.server_thread = Thread(target = self.server.serve_forever)
        #self.server_thread.daemon = True
        self.server_thread.setDaemon(conf.setDaemon)
        self.server_thread.start()
        log.info("Server is started on port %s", self.port)
