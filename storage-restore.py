# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Restoring from storage
@copyright 2009-2012, Maprox LLC
'''

import re
import socket
import time

from kernel.logger import log
from kernel.config import conf
from lib.storage import storage

try:
  timestamp = str(int(time.time()))
  for record in storage.load():
    host, port = "localhost", int(record['port'])
    for item in record['data']:
      try:
        # Connect to server and send data
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
          sock.connect((host, port))

          contents = item['contents'].split('\n')
          for line in contents:
            time.sleep(1)
            # В случае внезапного обрыва связи переподключаемся,
            # и пытаемся еще раз послать пакет
            try:
              sock.send(bytes(line, 'UTF-8'))
            except Exception as E:
              sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              sock.connect((host, port))
              sock.send(bytes(line, 'UTF-8'))

          storage.delete(item, record['port'], timestamp)
        except Exception as E:
          log.error(E)
        finally:
          sock.close()
      except Exception as E:
        log.error(E)
except Exception as E:
  log.error(E)
