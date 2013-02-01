# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Teltonika FMXXXX firmware
@copyright 2009-2013, Maprox LLC
'''

from lib.handlers.teltonika.abstract import TeltonikaHandler

class Handler(TeltonikaHandler):
    """ Teltonika. FMXXXX """
    _confSectionName = "teltonika.fmxxxx"


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
from lib.ip import get_ip
class TestCase(unittest.TestCase):

    def setUp(self):
        pass
