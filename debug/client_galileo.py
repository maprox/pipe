# -*- coding: utf8 -*-
'''
@auth: Maprox LLC © sunsay
@date: 2012.06.25
'''

import re
import socket

# ===========================================================================
# TESTS
# ===========================================================================

data = b'\x01\x17\x80\x01\n\x02w\x03868204000728070\x042\x00\x84\x90'

# Connect to server and send data
host, port = "localhost", 21001

try:
  # Create a socket (SOCK_STREAM means a TCP socket)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((host, port))
  sock.send(data)
  #sock.read()
  sock.close()
except Exception as E:
  print(E)
