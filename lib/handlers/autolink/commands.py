# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Autolink commands
@copyright 2013, Maprox LLC
"""

import socket
from lib.commands import *
from lib.factory import AbstractCommandFactory
from lib.handlers.autolink.packets import *

# ---------------------------------------------------------------------------

class AutolinkCommand(AbstractCommand):
    """
     Autolink command packet
    """

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