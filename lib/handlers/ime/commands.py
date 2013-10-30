# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Ime commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory

# ---------------------------------------------------------------------------

class ImeCommand(AbstractCommand):
    """
     Ime command packet
    """

# ---------------------------------------------------------------------------
class ImeCommandConfigure(ImeCommand, AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = False
    """ False if protocol doesn't support dns hostname (only ip-address) """

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        config = self._initiationConfig
        password = '123456'
        if transport == "sms":
            command0 = password + '*WCAS*' + \
                       config['host'] + ';' + str(config['port'])
            command1 = password + '*APNI*' + \
                       config['gprs']['apn'] \
                       + ';' + config['gprs']['username'] \
                       + ';' + config['gprs']['password']
            return [{
                "message": command0
            }, {
                "message": command1
            }]
        else:
            return super(ImeCommandConfigure, self).getData(transport)

# ---------------------------------------------------------------------------

class CommandFactory(AbstractCommandFactory):
    """
     Command factory
    """
    module = __name__

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        self.factory = CommandFactory()