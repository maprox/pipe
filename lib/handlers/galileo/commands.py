# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Galileo commands
@copyright 2013, Maprox LLC
"""

import socket
from lib.commands import *
from lib.factory import AbstractCommandFactory
from lib.handlers.naviset.packets import *

# ---------------------------------------------------------------------------

class GalileoCommand(AbstractCommand, NavisetBase):
    """
     Galileo command packet
    """

# ---------------------------------------------------------------------------

class GalileoCommandConfigure(GalileoCommand, AbstractCommandConfigure):
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
        password = '1234'
        if transport == "sms":
            command0 = 'ServerIp ' + config['host'] + ',' + str(config['port'])
            command1 = 'APN ' + config['gprs']['apn'] \
                       + ',' + config['gprs']['username'] \
                       + ',' + config['gprs']['password']
            return [{
                "message": "AddPhone " + password
            }, {
                "message": command0
            }, {
                "message": command1
            }]
        else:
            return super(GalileoCommandConfigure, self).getData(transport)

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

    def test_packetData(self):
        cmd = self.factory.getInstance({
            'command': 'configure',
            'params': {
                "identifier": "0123456789012345",
                "host": "trx.maprox.net",
                "port": 21001,
                "gprs": {
                    "apn": "tele237.msk"
                }
            }
        })
        self.assertEqual(cmd.getData('sms'), [
            {'message': 'AddPhone 1234'},
            {'message': 'ServerIp trx.maprox.net,21001'},
            {'message': 'APN tele237.msk,,'}
        ])
