# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Project tests
@copyright 2009-2013, Maprox LLC
'''

import unittest

from lib.handlers.galileo.tags import TestCase as tc0
from lib.handlers.galileo.packets import TestCase as tc1
from lib.handlers.galileo.abstract import TestCase as tc2
from lib.crc16 import TestCase as tc3
from lib.handlers.naviset.packets import TestCase as tc4
from lib.handlers.naviset.abstract import TestCase as tc5
from lib.handlers.naviset.gt10 import TestCase as tc6
from lib.handlers.naviset.gt20 import TestCase as tc7
from lib.handlers.globalsat.abstract import TestCase as tc8
from lib.handlers.globalsat.tr151 import TestCase as tc9
from lib.handlers.globalsat.tr203 import TestCase as tc10
from lib.handlers.globalsat.tr206 import TestCase as tc11
from lib.handlers.globalsat.tr600 import TestCase as tc12
from lib.handlers.globalsat.gtr128 import TestCase as tc12a
from lib.handlers.teltonika.abstract import TestCase as tc13
from lib.handlers.teltonika.fmxxxx import TestCase as tc14
from lib.handlers.teltonika.packets import TestCase as tc15
from lib.handlers.atrack.abstract import TestCase as tc16

if __name__ == '__main__':
    unittest.main()
