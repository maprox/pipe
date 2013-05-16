# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack AX5 firmware
@copyright 2013, Maprox LLC
'''

from lib.handlers.atrack.abstract import AtrackHandler

class Handler(AtrackHandler):
    """ ATrack. AX5 """
    _confSectionName = "atrack.ax5"


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass