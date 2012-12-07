# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Restoring from storage
@copyright 2009-2012, Maprox LLC
'''

import socket
import time

from kernel.logger import log
from lib.storage import storage

try:
    timestamp = str(int(time.time()))
    for record in storage.load():
        host, port = "localhost", int(record['port'])
        for item in record['data']:
            try:
                data = item['contents']
                # Connect to server and send data
                # Create a socket (SOCK_STREAM means a TCP socket)
                sock = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )
                try:
                    sock.connect((host, port))
                    try:
                        sock.send(data)
                    except Exception as E:
                        # In case of error during data sending
                        # try to send it again
                        sock = socket.socket(
                            socket.AF_INET,
                            socket.SOCK_STREAM
                        )
                        sock.connect((host, port))
                        sock.send(data)

                    storage.delete(item, str(port), timestamp)
                except Exception as E:
                    log.error(E)
                finally:
                    sock.close()
            except Exception as E:
                log.error(E)
except Exception as E:
    log.error(E)
