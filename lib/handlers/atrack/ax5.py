# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      ATrack AX5 firmware
@copyright 2013, Maprox LLC
'''

from lib.handlers.atrack.abstract import AtrackHandler

class Handler(AtrackHandler):
    """ ATrack. AX5 """
    pass

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = Handler(pipe.Manager(), None)

    def test_config(self):
        h = self.handler
        self.assertEqual(h.getConfigOption('positionReportPrefix', '@P'), '@P')
