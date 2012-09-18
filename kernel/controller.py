# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Управляющий модуль
@copyright 2009-2012 © Maprox Ltd.
'''

from kernel.logger import log
from kernel.database import db

# ===========================================================================
class Controller(object):
  '''
   Центральный класс, запускающий tcp-сервер
   и остальные компоненты обсервера.
  '''

  # -----------------------------
  def __init__(self):
    'Конструктор класса Starter'
    log.debug('Starter::__init__')

  # -----------------------------
  def run(self):
    'Запуск основного цикла приложения'
    log.debug('Starter::run()')
    try:
      Server(conf.port).run()
    except Exception as E:
      log.critical(E)
