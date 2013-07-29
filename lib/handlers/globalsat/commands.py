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

class GloblasatCommandConfigure(AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = False
    """ False if protocol doesn't support dns hostname (only ip-address) """

    def getSmsData(self, config):
        """
         Converts options to string
         @param config: request data
         @return: string
        """
        initialConfig = conf.get('settings', 'initialConfig')
        if initialConfig:
            initialConfig = ',' + initialConfig
        ret = "GSS,{0},3,0".format(config['identifier'])
        ret += ',O3=' + conf.get('settings', 'reportFormat')
        ret += initialConfig
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

class CommandActivateDigitalOutput(AbstractCommand):
    """
     Activates digital output by number
    """
    alias = 'activate_digital_output'

    __outputNumber = 0

    @property
    def outputNumber(self):
        return self.__outputNumber

    @outputNumber.setter
    def outputNumber(self, value):
        if 0 <= value <= 15:
            self.__outputNumber = value

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.outputNumber = int(dictCheckItem(params, 'outputNumber', 0))

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        return "Lo(%d,1)" % self.outputNumber

# ---------------------------------------------------------------------------

class CommandDeactivateDigitalOutput(CommandActivateDigitalOutput):
    """
     Deactivates digital output by number
    """
    alias = 'deactivate_digital_output'

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        return "Lo(%d,0)" % self.outputNumber

# ---------------------------------------------------------------------------

class CommandRestart(AbstractCommand):
    alias = 'restart_tracker'

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        return "LH"

# ---------------------------------------------------------------------------

class CommandCustom(AbstractCommand):
    alias = 'custom'

    __message = None

    @property
    def message(self):
        return self.__message

    @message.setter
    def message(self, value):
        self.__message = value

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.message = dictCheckItem(params, 'message', '')

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        return self.message

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
                'O3=' + conf.get('settings', 'reportFormat') + ',' +\
                conf.get('settings', 'initialConfig') + \
                ',D1=,D2=,D3=,E0=trx.maprox.net,E1=21202*0A!'
        }])

    def test_digitalOutputs(self):
        cmd = self.factory.getInstance({
            'command': 'activate_digital_output',
            'params': {
                'outputNumber': 2
            }
        })
        self.assertEqual(cmd.getData('sms'), 'Lo(2,1)')

    def test_customMessage(self):
        cmd = self.factory.getInstance({
            'command': 'custom',
            'params': {
                'message': 'SOME CUSTOM COMMAND'
            }
        })
        self.assertEqual(cmd.getData('tcp'), 'SOME CUSTOM COMMAND')