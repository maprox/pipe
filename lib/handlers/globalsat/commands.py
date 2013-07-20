# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globalsat commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory
import lib.handlers.globalsat.packets as packets

# ---------------------------------------------------------------------------

class GlobalsatCommand(AbstractCommand):
    """
     Teltonka command packet
    """
    pass

# ---------------------------------------------------------------------------

class GloblasatCommandConfigure(GlobalsatCommand, AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = False
    """ False if protocol doesn't support dns hostname (only ip-address) """

    def getSmsData(self, config):
        """
         Converts options to string
         @param options: options
         @param config: request data
         @return: string
        """
        ret = "GSS,{0},3,0".format(config['identifier'])
        ret += ',O3=' + conf.get('settings', 'reportFormat')
        ret += conf.get('settings', 'initialConfig')
        ret += ',D1=' + str(config['gprs']['apn'] or '')
        ret += ',D2=' + str(config['gprs']['username'] or '')
        ret += ',D3=' + str(config['gprs']['password'] or '')
        ret += ',E0=' + str(config['host'] or '')
        ret += ',E1=' + str(config['port'] or '')
        ret = packets.addChecksum(ret)
        return [{
            "message": ret
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
            return super(GloblasatCommandConfigure, self).getData(transport)

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
        conf.read('conf/handlers/globalsat.tr600.conf')
        self.factory = CommandFactory()

    def test_packetData(self):
        cmd = self.factory.getInstance({
            'command': 'configure',
            'params': {
                "identifier": "0123456789012345",
                "host": "trx.maprox.net",
                "port": 21202
            }
        })
        self.assertEqual(cmd.getData('sms'), [{
            'message': 'GSS,0123456789012345,3,0,' + \
                'O3=' + conf.get('settings', 'reportFormat') +\
                conf.get('settings', 'initialConfig') + \
                ',D1=,D2=,D3=,E0=trx.maprox.net,E1=21202*26!'
        }])