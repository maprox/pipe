# -*- coding: utf8 -*-
'''
@auth: Maprox Ltd © sunsay
@date: 2009.07.06
@info: Клиент для тестов
'''

import re
import socket

def getChecksum(data):
  """
   Returns the data checksum
   @param data: data string
   @return: hex string checksum
  """
  csum = 0
  for c in data:
      csum ^= ord(c)
  hex_csum = "%02X" % csum
  return hex_csum

data = "GSr,357460032240926,00,4,e000,e000,3,270711,045943,E05032.8735,N5341.6164,109,17.95,0,11,0.8,13020,12910mV,0,0,0,0,0,555228,0"
fmt =  "    S               P R A  B             2  7GHKLMNO*U!"
data = 'GSd,354660045082859,8,g,00,120911,204306,31,"250,02,1E4A,2B4F,77,10","250,02,1E4A,2B50,07,10","250,02,1E4A,92FD,20,6","250,02,1E4A,282B,43,6","250,02,1E4A,2826,73,5"*38!'
data = data + "*" + getChecksum(data) + "!"

#SPRXYAB27GHKLMmnaefghio*U!

# Connect to server and send data
host, port = "trx.maprox.net", 20100

try:
  # Create a socket (SOCK_STREAM means a TCP socket)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((host, port))
  sock.send(bytes(data, "ascii"))
  sock.close()
except Exception as E:
  print(E)
