# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset GT-20 firmware
@copyright 2009-2012, Maprox LLC
'''

from lib.handlers.naviset.abstract import NavisetHandler

class Handler(NavisetHandler):
    """ Naviset. GT-20 """
    _confSectionName = "naviset.gt20"


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_format(self):
        import kernel.pipe as pipe
        import json
        h = Handler(pipe.Manager(), None)
        h.processCommandFormat('format', json.dumps({
            "host": "trx.maprox.net",
            "port": None,
            "gprs": {
                "apn": "internet",
                "username": None,
                "password": None
            }
        }))