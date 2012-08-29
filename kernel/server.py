# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net>
@info      TCP-server
@copyright 2009-2012, Maprox LLC
'''

import traceback
from threading import Thread
from socketserver import TCPServer
from socketserver import ThreadingMixIn
from socketserver import BaseRequestHandler

from kernel.logger import log
from kernel.config import conf
from kernel.dispatcher import disp


# ===========================================================================
class ClientThread(BaseRequestHandler):
  '''
   Класс потомок RequestHandler'а для нашего сервера.
   Объект данного класса создается на каждое соединение с сервером извне.
   Мы переопределяем метод handle и в нем "общаемся" с клиентом
  '''

  def setup(self):
    pass

  def handle(self):
    try:
      disp.dispatch(self)
    except Exception as E:
      log.error("Dispatch error: %s", traceback.format_exc())

  def finish(self):
    pass

# ===========================================================================
class ThreadingServer(ThreadingMixIn, TCPServer):
  'Базовый класс, который добавляет многопоточность к TCP-серверу'
  allow_reuse_address = True


# ===========================================================================
class Server():
  """ Multithreaded TCP-server """

  # -----------------------------
  def __init__(self, port = 30003):
    """
     Server class constructor
     @param port: Listening port. Optional, default is 30003.
    """
    log.debug("Server::__init__(%s)", port)
    self.host = ""
    self.port = port
    self.server = ThreadingServer((self.host, self.port), ClientThread)

  # -----------------------------
  def run(self):
    """ Method wich starts TCP-server """
    log.debug("Server::run()")
    # Запускаем нить сервера - эта нить затем будет создавать
    # остальные нити для каждого подключения
    self.server_thread = Thread(target = self.server.serve_forever)
    # Не завершаем работу сервера даже если основная нить завершилась
    # (такого [завершение основной нити] при работе 24/7 быть не должно)
    self.server_thread.setDaemon(conf.setDaemon)
    self.server_thread.start()
    # Пишем немного информации в лог файл
    log.info("Server is started on port %s", self.port)

  # -----------------------------
  def verify_request(self, request, client_address):
    'Проверка запроса в списке IP'
    log.debug("verify_request()")
    return True
