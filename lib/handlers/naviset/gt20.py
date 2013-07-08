# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset GT-20 firmware
@copyright 2009-2012, Maprox LLC
'''

from lib.handlers.naviset.abstract import NavisetHandler

class Handler(NavisetHandler):
    """ Naviset. GT-20 """
    pass


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
        #h = Handler(pipe.Manager(), None)
        #h.processCommandFormat(116363, json.dumps({
        #    "host":"observer.localhost",
        #    "port":21100,
        #    "identifier":"012896001609129",
        #    "gprs":{"apn":"internet","username":"","password":""}
        #}))