# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Ime commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory
import lib.handlers.ime.packets as packets

# ---------------------------------------------------------------------------

class ImeCommand(AbstractCommand, packets.ImePacket):
    """
     Ime command packet
    """
    _header = 0x4040      # @@ - prefix of the packet (can be $$ or @@)

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.deviceImei = params['identifier'] or 0
        return super(ImeCommand, self).setParams(params)

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        if transport == "tcp":
            return self.rawData
        return []

# ---------------------------------------------------------------------------

class ImeCommandConfigure(ImeCommand, AbstractCommandConfigure):
    alias = 'configure'

    hostNameNotSupported = True
    """ True if protocol doesn't support dns hostname (only ip-address) """

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        config = self._initiationConfig
        password = '000000'
        if transport == "sms":
            command0 = 'W' + password + ',010,' + config['identifier']
            command1 = 'W' + password + ',011,' + \
                       config['gprs']['apn'] \
                       + ',' + config['gprs']['username'] \
                       + ',' + config['gprs']['password']
            command2 = 'W' + password + ',013,1'
            command3 = 'W' + password + ',012,1,' + \
                       config['host'] + ',' + str(config['port'])
            return [
                {"message": command0},
                {"message": command1},
                {"message": command2},
                {"message": command3}
            ]
        else:
            return super(ImeCommandConfigure, self).getData(transport)

# ---------------------------------------------------------------------------

class ImeCommandLoginConfirm(ImeCommand):
    """
     Server sends this command back to the tracker to confirm tracker’s login.
    """
    alias = 'login_confirm'

    __success = None
    _command = packets.CMD_LOGIN_CONFIRMATION       # expected command number

    def setParams(self, params):
        """
         Initialize command with params
         @param params:
         @return:
        """
        self.success = dictCheckItem(params, 'success', True)
        return super(ImeCommandLoginConfirm, self).setParams(params)

    def _buildBody(self):
        """
         Builds body of the packet
         @return: body binstring
        """
        body = super(ImeCommandLoginConfirm, self)._buildBody()
        body += pack('>B', 0x01 if self.success else 0x00)
        return body

    @property
    def success(self):
        if self._rebuild: self._build()
        return self.__success

    @success.setter
    def success(self, value):
        self.__success = value
        self._rebuild = True

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
from lib.crc16 import Crc16
class TestCase(unittest.TestCase):

    def setUp(self):
        packets.ImeBase.fnChecksum = Crc16.calcCCITT
        packets.ImeBase._fmtChecksum = '>H'
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
        self.assertIsInstance(cmd, ImeCommandConfigure)
        self.assertEqual(cmd.getData('sms'), [
            {'message': 'W000000,012,1,trx.maprox.net,21001'},
            {'message': 'W000000,011,tele237.msk,,'}
        ])


    def test_commandLoginConfirm(self):
        cmd = self.factory.getInstance({
            'command': 'login_confirm',
            'params': {
                'identifier': '123456'
            }
        })
        self.assertIsInstance(cmd, ImeCommandLoginConfirm)
        self.assertEqual(cmd.getData(),
            b'@@\x00\x12\x12\x34\x56\xFF\xFF\xFF\xFF\x40\x00\x01\xA9\x9B\r\n')
