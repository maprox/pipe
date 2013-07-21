# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globalsat TR151 commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory

# ---------------------------------------------------------------------------

class GloblasatTR151CommandConfigure(AbstractCommandConfigure):
    alias = 'configure'

    def getSmsData(self, config):
        """
         Converts options to string
         @param options: options
         @param config: request data
         @return: string
        """
        message = '?7,' + config['identifier'] + ',7,'\
           + str(config['port']) + ','\
           + config['gprs']['apn'] + ','\
           + config['gprs']['username'] + ','\
           + config['gprs']['password'] + ','\
           + '' + ','\
           + '' + ','\
           + config['host'] + '!'
        return [{
            'message': message
        }]

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        if transport == "sms":
            return self.getSmsData(self._initiationConfig)
        else:
            return super(GloblasatTR151CommandConfigure,
                self).getData(transport)

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
        conf.read('conf/handlers/globalsat.tr151.conf')
        self.factory = CommandFactory()

    def test_packetData(self):
        cmd = self.factory.getInstance({
            'command': 'configure',
            'params': {
                "identifier": "0123456789012345",
                "host": "trx.maprox.net",
                "port": 21200
            }
        })
        self.assertEqual(cmd.getData('sms'), [{
            'message': '?7,0123456789012345,7,21200,,,,,,trx.maprox.net!'
        }])