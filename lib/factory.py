# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Abstract class for packet factory
@copyright 2013, Maprox LLC
'''

class AbstractPacketFactory:
    """
     Abstract packet factory
    """
    config = None

    def __init__(self, config = None):
        """
         Constructor of Packet Factory.
         @param params: Factory parameters
        """
        self.config = config

    def getPacketsFromBuffer(self, data = None):
        """
         Returns an array of BasePacket instances from data
         @param data: Input binary data
         @return: array of BasePacket instances (empty array if no packet found)
        """
        packets = []
        while True:
            packet = self.getInstance(data)
            if not packet: break
            data = packet.rawDataTail
            packets.append(packet)
            if not data or len(data) == 0: break
        return packets

    def getInstance(self, data):
        """
          Returns a packet instance by supplied data
          @return: BinaryPacket
        """
        return None
