# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Globalsat TR-151
@copyright 2009-2012, Maprox LLC
'''

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handler import AbstractHandler


class Handler(AbstractHandler):
    """ Globalsat. TR-151 """

    confSectionName = "globalsat.tr151"
    reportFormat = "SPRAB27GHKLMNO*U!"

    re_patterns = {
        'line': '\$(?P<line>(?P<head>GS\w){fields})\*!',
        'report': "(?P<code>\d+),(?P<uid>\w+)"
    }

    def __init__(self, store, thread):
        """ Constructor """
        AbstractHandler.__init__(self, store, thread)

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
        """
        # let's work with text data
        data = data.decode('utf-8')

        rc = re.compile(self._, flags = re.IGNORECASE)


    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
         @param packet: a L{packets.Packet} subclass
        """
        buf = self.getAckPacket(packet)
        log.info("Send acknowledgement, crc = %d" % packet.crc)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, packet):
        """
         Returns acknowledgement buffer value
         @param packet: Received packet
        """
        return b"$OK!"
