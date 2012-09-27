# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Запускающий модуль
@copyright 2009-2011 © Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/kernel/starter.py $
@version   $Id: starter.py 400 2011-02-20 22:06:46Z sunsay $
'''

from kernel.logger import log
from kernel.config import conf
from kernel.server import Server

# ===========================================================================
class Starter(object):
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
