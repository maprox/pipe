# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Naviset GT-20 firmware
@copyright 2009-2012, Maprox LLC
'''

import re
import socket

# ===========================================================================
# TESTS
# ===========================================================================


data = b'SAMPLE'

# Connect to server and send data
host, port = "localhost", 21300

try:
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(data)
    sock.recv(4096)
    #print(sock.recv(4096))
    #sock.send(data2)
    sock.close()
except Exception as E:
    print(E)
