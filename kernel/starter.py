# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Server starter class
@copyright 2009-2016, Maprox LLC
"""

from kernel.logger import log
from kernel.config import conf
from kernel.server import Server


class Starter:
    """
     Base Class that starts tcp-server and other components.
    """

    @staticmethod
    def run():
        """
         Start of main cycle of the application
        """
        log.debug('Starter::run()')
        try:
            Server(conf.port).run()
        except Exception as E:
            log.critical(E)
