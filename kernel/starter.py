# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Server starter class
@copyright 2009-2011, Maprox LLC
'''

from kernel.logger import log
from kernel.config import conf
from kernel.server import Server

# ===========================================================================
class Starter(object):
    """
     Base Class that starts tcp-server and other components.
    """

    # -----------------------------
    def __init__(self):
        """
         Constructor
        """
        log.debug('Starter::__init__')

    # -----------------------------
    def run(self):
        """
         Start of main cycle of the application
        """
        log.debug('Starter::run()')
        try:
            Server(conf.port).run()
        except Exception as E:
            log.critical(E)
