# -*- coding: utf8 -*-
'''
@auth: Maprox Ltd © sunsay
@date: 2009.07.06
@info: Клиент для тестов
'''

import re
import socket

def coordEncode(coord):
  res = coord[:2]
  tail = '0' + coord[2:]
  tail = 60 * float(tail)
  if tail < 10:
    res += '0' + str(tail)
  else:
    res += str(tail)
  return res

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

uid = '356051037867929'
speed = '20.00'
pdate = '220211'
ptime = '151510.982'

lat = '53.38002619818837'
lng = '50.17670631408691'

clat = coordEncode(lat)
clng = coordEncode(lng)

print(clat + ', ' + clng)

#data = "716460046473420|8000|5331.0136|N|04917.2428|E|0.00|351.18|311007|185614.982|";
#data = "716460046473421|8888|5331.0136|N|04917.2428|E|0.00|351.18|301007|185612.982|";
#data = "716460046473421|8888|5332.0136|N|04937.2428|E|0.00|351.18|041109|185612.982|";
#data = "716460046473421|8888|5316.2280|N|05016.2160|E|60.00|351.18|200410|212758.982|";

#data  = uid + "|8888|" + clat + "|N|" + clng + "|E|"
#data += speed + "|351.18|" + pdate + "|" + ptime + "|"
#data = "GSr,357460032240926,00,5,e080,e080,3,220611,103641,E05012.3487,N5314.3791,153,19.17,36,8,0.8,13610,13460mV,0,0,0,0,0,7023,0*50!"
#s = "GSr,357460032240926,00,6,e080,e080,3,220611,105314,E05012.6060,N5314.5480,155,1.13,46,6,1.6,13790,13670mV,0,0,0,0,0,7603,0*6e!"
s = "GSr,357460032240926_888,00,6,e000,e000,3,050711,143314,E05012.6060,N5314.5480,155,1.13,46,6,1.6,13790,13670mV,0,0,0,0,0,7603,0"
checksum = getChecksum(s)
data = s + "*" + checksum + "!"
print(data)

# Connect to server and send data
host, port = "localhost", 20100

try:
  # Create a socket (SOCK_STREAM means a TCP socket)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((host, port))
  sock.send(bytes(data + "\r\n", "ascii"))
  sock.close()
except Exception as E:
  print(E)
