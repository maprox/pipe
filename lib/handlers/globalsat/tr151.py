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

    def __init__(self, store, thread):
        """ Constructor """
        AbstractHandler.__init__(self, store, thread)

    def dispatch(self):
        """
         Dispatching data from socket
        """
        log.debug("Recieving...")
        buffer = self.recv()
        while len(buffer) > 0:
            self.processData(buffer)
            buffer = self.recv()

        return super(Handler, self).dispatch()

    def getFunction(self, data):
        """
         Returns a function name according to supplied data
         @param data: data string
         @return: function name
        """
        data_type = data[:4]
        if data_type == '$OK!':
            return "processSettings"
        elif data_type == 'GSr':
            return "processData"
        else:
            raise NotImplementedError("Unknown data type" + data_type)

    def processData(self, data):
        """
         Processing of data from socket / storage.
         @param data: Data from socket
        """
        rc = self.re_compiled['report']
        position = 0

        m = rc.search(data, position)
        if not m:
            self.processError(data)

        while m:
            # - OK. we found it, let's see for checksum
            log.debug("Raw match found.")
            data_device = m.groupdict()
            cs1 = str.upper(data_device['checksum'])
            cs2 = str.upper(self.getChecksum(data_device['line']))
            if (cs1 == cs2):
                data_observ = self.translate(data_device)
                data_observ['__rawdata'] = m.group(0)
                log.info(data_observ)
                self.uid = data_observ['uid']
                store_result = self.store([data_observ])
                if data_observ['sensors']['sos'] == 1:
                    self.stopSosSignal()
            else:
                log.error("Incorrect checksum: %s against computed %s",
                          cs1, cs2)
            position += len(m.group(0))
            m = rc.search(data, position)

        return super(GlobalsatHandler, self).processData(data)
