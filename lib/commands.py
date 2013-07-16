# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Abstract commands
@copyright 2013, Maprox LLC
'''

from lib.packets import BasePacket

# ---------------------------------------------------------------------------

class AbstractCommand(object):
    """
     Protocol command
    """
    _alias = None
    _params = None
    """ Command alias """

    def __init__(self, params = None):
        if params:
            self._params = params

class TextCommand(AbstractCommand):
    """
     Simple text protocol command
    """
    pass

class BinaryCommand(BasePacket, AbstractCommand):
    """
     Abstract binary protocol command with length and checksum
    """
    pass