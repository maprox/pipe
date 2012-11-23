# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset GT-10 firmware
@copyright 2009-2012, Maprox LLC
'''

from lib.handlers.naviset.abstract import NavisetHandler

class Handler(NavisetHandler):
    """ Naviset. GT-10 """
    _confSectionName = "naviset.gt10"

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        pass
