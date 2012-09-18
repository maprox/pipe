# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Управляющий модуль
@copyright 2009-2012 © Maprox Ltd.
'''

from kernel.logger import log
from kernel.dbmanager import db

# ===========================================================================
class Controller(object):
  '''
   Класс управляющий Pipe-сервером
  '''

  # -----------------------------
  def __init__(self):
    'Конструктор класса Controller'
    log.debug('Controller::__init__')

  # -----------------------------
  def run(self):
    'Запуск проверки комманд на выполнение'
    log.debug('Controller::run()')
    try:
      commands = db.getController().getCommands()
      log.info(commands)
    except Exception as E:
      log.critical(E)
