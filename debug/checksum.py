# -*- coding: utf8 -*-
'''
@auth: Maprox Ltd. (sunsay)
@date: 2011
@info: Checksum output
'''

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


s = "GSS,354660044558446,3,0,Ri=30"
s = "GSC,357460032240926,L1(O3)"
s = "GSS,357460032240926,3,0,F0=89277028368"
s = "GSS,011412001418924,3,0,D1=internet,D2=gdata,D3=gdata,O3=SPRAB27GHKLMNO*U!,O8=1,E0=trx.maprox.net,E1=20203,F0=89277028368"
#s = "GSS,3519960467506531,3,0,D1=internet.mts.ru,D2=,D3=,O3=SPRXYAB27GHKLMmnaefghio*U!"
checksum = getChecksum(s)
data = s + "*" + checksum + "!"
print(data)