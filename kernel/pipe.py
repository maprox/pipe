# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Class implements communication with pipe-controller
@copyright 2009-2013, Maprox LLC
'''

from kernel.logger import log
from kernel.config import conf
from kernel.store import Store

import json
import urllib.parse
import urllib.request

import lib.falcon
from lib.broker import broker

# RabbitMQ processing features


class Manager(Store):
    """
     Class implements communication with pipe-controller
    """

    def send(self, obj):
        """
         Sending data to the controller receiving packets from the devices
        """
        result = lib.falcon.FalconAnswer()
        try:
            packets = list()
            if (isinstance(obj, list)):
                # if multiple packets
                packets = obj
            elif (isinstance(obj, dict)):
                # if one packet
                packets.append(obj)
            else:
                return result
            # Let's create url_data object
            url_data = {'data' : json.dumps({
              'key': conf.pipeKey,
              'packets': packets
            })}
            # Let's send packets to AMQP broker
            self.sendPacketsViaBroker(packets)
        except Exception as E:
            result.error('500', ['Error sending packets: ' + str(E)])
            log.error(E)
        return result

    def sendPacketsViaBroker(self, packets):
        """
         Sends data to the message broker (AMQP)
         @param packets: list of packets
         @return:
        """
        try:
            broker.sendPackets(packets)
        except Exception as E:
            #~print(E)
            log.error(E)

class TestManager(Manager):
    stored_packets = []

    def __init__(self):
        self.stored_packets = []
        super(TestManager, self).__init__

    def send(self, obj):
        result = lib.falcon.FalconAnswer()
        packets = list()
        if (isinstance(obj, list)):
            # if multiple packets
            packets = obj
        elif (isinstance(obj, dict)):
            # if one packet
            packets.append(obj)
        self.stored_packets.extend(packets)
        return result

    def get_stored_packets(self):
        return self.stored_packets