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
        #    "port":21200,
        #    "identifier":"012896001609129",
        #    "gprs":{"apn":"internet","username":"","password":""}
        #}))