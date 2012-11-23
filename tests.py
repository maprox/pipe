# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Project tests
@copyright 2009-2012, Maprox LLC
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

if __name__ == '__main__':
    unittest.main()
