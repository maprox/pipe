# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Abstract class for packet factory
@copyright 2013, Maprox LLC
'''

from lib.commands import *

# ---------------------------------------------------------------------------

class AbstractFactory:
    """
     Abstract factory
    """
    config = None

    def __init__(self, config = None):
        """
         Constructor of Factory.
         @param params: Factory parameters
        """
        self.config = config or {}

    def getInstance(self, data):
        """
          Returns a packet instance by supplied data
          @param data: some data
          @return: BinaryPacket
        """
        return None

# ---------------------------------------------------------------------------

class AbstractPacketFactory(AbstractFactory):
    """
     Abstract packet factory
    """
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

# ---------------------------------------------------------------------------

class AbstractCommandFactory(AbstractFactory):
    """
     Abstract command factory
    """
    module = None

    def getInstance(self, data):
        """
          Returns a command instance by supplied data
          @param data: dict command description
          @return: AbstractCommand
        """
        if not data or not self.module:
            return None

        commandClassName = getCommandClassByAlias(data["command"], self.module)
        if commandClassName:
            params = {} if not "params" in data else data["params"]
            return commandClassName(params)
        else:
            return None
