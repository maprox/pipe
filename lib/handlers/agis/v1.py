# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Протокол AGIS-V1
@copyright 2009-2011 © Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/lib/listeners/agis/v1.py $
@version   $Id: v1.py 404 2011-02-24 22:16:22Z sunsay $
'''

import re
from datetime import datetime

from kernel.logger import log
from kernel.config import conf
from lib.handler import AbstractHandler

# Регулярное выражение, которому должна соответствовать каждая
# запись, переданная модемом нашему серверу
regex = '^(\d+)\|(\d{4})\|'           # идентификатор, код сообщения
regex += '(\d+\.\d+)\|(N|S|W|E)\|'    # широта
regex += '(\d+\.\d+)\|(N|S|W|E)\|'    # долгота
regex += '(\d+\.\d+)\|(\d+\.\d+)\|'   # скорость, азимут
regex += '(\d{6})\|(\d+\.?\d+)\|'     # дата, время посылки

regexCoord = '(\d{2,})(\d{2}.\d{2,})' # координаты протокола A-GIS v1

class Handler(AbstractHandler):
  'AGIS. v1'

  def __init__(self, store = None):
    'Инициализация объекта. Создаем объект работы с хранилищем'
    Listener.__init__(self, store)

  def dispatch(self, clientThread):
    'Обработка данных, поступивших от модема'
    Listener.dispatch(self, clientThread)
    data = clientThread.request.recv(conf.initDataCount)
    while len(data) > 0:
      matchObj = re.match(regex, data.decode());
      self.store(matchObj)
      data = clientThread.request.recv(4096)

  def coordCalc(self, coord, letter):
    mo = re.match(regexCoord, coord)
    result = str(int(mo.group(1)))
    result += str(float(mo.group(2)) / 60)[1:]
    if (letter.upper() == 'W' or letter.upper() == 'S'):
      result = '-' + result
    return result

  def store(self, matchObject):
    """Сохранение обработанных данных в хранилище"""
    log.debug('%s::store()', self.__class__)
    try:
      mo = matchObject
      packet = dict()
      packet['uid'] = mo.group(1)
      packet['latitude'] = self.coordCalc(mo.group(3), mo.group(4))
      packet['longitude'] = self.coordCalc(mo.group(5), mo.group(6))
      packet['code'] = mo.group(2)
      packet['speed'] = mo.group(7)
      packet['azimuth'] = mo.group(8)
      # вычисляем время
      timeStr = matchObject.group(9) + ' ' + matchObject.group(10)
      dt = datetime.strptime(timeStr, '%d%m%y %H%M%S.%f')
      packet['time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
      self.send([packet])
      # закрываем соединение
    except Exception as E:
      log.error(E)
