# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Teltonika commands
@copyright 2013, Maprox LLC
"""

from lib.commands import *
from lib.factory import AbstractCommandFactory
from lib.handlers.teltonika.packets import *

# ---------------------------------------------------------------------------



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
                "port": 21202
            }
        })
        self.assertEqual(cmd.getData('sms'), [
            {'message': 'COM3 1234,trx.maprox.net,21200'},
            {'message': 'COM13 1234,1,,,#'}
        ])