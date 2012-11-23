# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Протокол AGIS-V2
@copyright 2009-2011, Maprox LLC
'''

from kernel.logger import log
from kernel.converters import intToBytes
from lib.handler import AbstractHandler

class Handler(AbstractHandler):
    """
     AGIS. Протокол 2
    """

    @classmethod
    def canDispatch(self, data):
        # проверяем длину входной строки
        if (len(data) < 4):
            return False
        # проверяем присланные данные SESSION_SETUP (или SESSION_ACK)
        """
          0x00  0x01
          0x01  0x01 (или 0x02)
          0x02     N
          0x03-0x0[3+N]
        """
        if (data[0] == 1) and (data[1] in [1, 2]):
            N = data[2]
            return N == len(data[3:])
        return False

    def __init__(self):
        """
         Инициализация объекта. Создаем объект работы с хранилищем
        """
        log.debug('AGIS_2_0::__init__()')
        self.session = False
        self.storage = Storage()

    def packetCreate(self, b1, b2, value):
        return bytes([b1, b2, len(value)]) + value

    def packetSessionNAK(self):
        return self.packetCreate(1, 3, bytes())

    def packetSessionACK(self):
        return self.packetCreate(1, 2, bytes())

    def packetSessionACK(self, sessionId):
        return self.packetCreate(1, 2, intToBytes(sessionId, 4))
   
    def dispatch(self, clientThread, data):
        """
         Обработка данных, поступивших от модема
        """
        log.debug('AGIS_2_0::dispatch()')
        """
        if data[0] == 1 and data[1] == 1:
          # SESSION_SETUP
          self.sessionSetup()
        else:
          # SESSION_ACK
          self.sessionAck()
        log.debug(self.packetSessionACK(1024))
        """
    #    while len(data) > 0:
    #      clientThread.send(
    #      data = clientThread.request.recv(4096)
