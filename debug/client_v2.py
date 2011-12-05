# -*- coding: utf8 -*-
'''
@auth: Maprox Ltd © sunsay
@date: 2009.07.06
@info: Клиент для тестов
'''

import time
import socket




def packetCreate(b1, b2, value):
  return bytes([b1, b2, len(value)]) + value

def packetSessionNAK():
  return packetCreate(1, 3, bytes())

def packetSessionACK():
  return packetCreate(1, 2, bytes())

def packetSessionACK():
  return packetCreate(1, 2, intToBytes(sessionId, 4))

def packetSessionSetup(modemId):
  return packetCreate(1, 2, modemId)

# Connect to server and send data
host, port = "localhost", 8765
data = "716460046473420|8888|5331.0136|N|04917.2428|E|0.00|351.18|301007|185612.982|";
data2 = "716460046473420|8888|5331.0236|N|04917.2428|E|0.00|351.18|301007|185612.982|";
data3 = "716460046473420|8888|5331.0336|N|04917.2428|E|0.00|351.18|301007|185612.982|";

try:
  # Create a socket (SOCK_STREAM means a TCP socket)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((host, port))
  sock.send(packetSessionSetup(b'716460046473420'))
  time.sleep(2)
#  sock.send(bytes(data + "\n", "ascii"))
#  sock.send(bytes(data + "\n", "ascii"))
  sock.close()
except Exception as E:
  print(E)