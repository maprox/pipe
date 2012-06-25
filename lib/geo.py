# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Abstract class for working with Geo coordinates
@copyright 2009-2012, Maprox Ltd.

Some links for smoking:
  http://www.earthpoint.us/Convert.aspx
  http://www.movable-type.co.uk/scripts/latlong.html
'''

import re

class Geo(object):
  """ Abstract class for working with Geo coordinates """

  """
   ---------------------------------------------------------------
   RegEx strings for decimal coordinates format, i.e.
   lat: 89.399397   ;  -77.987750  ;  0.987561  ;  -90
   lon: 123.098777  ;  030.330033  ;  179.0000  ; -180
  """
  ' ===== LATITUDE ===== '
  re_dec_lat_max = '^(?P<val>-90(?:\.(0*))?)$'
  re_dec_lat = '^(?P<val>(-?[0-8]?\d)?(?:\.(\d*))?)$'

  ' ===== LONGITUDE ===== '
  re_dec_lon_max = '^(?P<val>-180(?:\.(0*))?)$'
  re_dec_lon = '^(?P<val>(-?(?:1[0-7]\d|0?\d{1,2}))?(?:\.(\d*))?)$'

  """
   ---------------------------------------------------------------
   RegEx strings for DDMM.MM coordinates format, i.e.
   lat:  3857.804N   ;   N7930.0045  ;   -3933.3334
   lon: 09515.739W   ;  E11122.0366  ;  -10239.9900
  """
  ' ===== LATITUDE ===== '
  r_ddmm_lat_max = '(?P<deg>90)(?P<min>00(?:\.(0*))?)'
  re_ddmm_lat_max_dir_l = '^(?P<dir>S)\s*' + r_ddmm_lat_max + '$'
  re_ddmm_lat_max_dir_r = '^' + r_ddmm_lat_max + '\s*(?P<dir>S)$'
  re_ddmm_lat_max_dir_s = '^(?P<dir>-)' + r_ddmm_lat_max + '$'

  r_ddmm_lat = '(?P<deg>[0-8]\d)'\
    '(?P<min>((?P<maxmin>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?))'
  re_ddmm_lat_dir_l = '^(?P<dir>[NS])\s*' + r_ddmm_lat + '$'
  re_ddmm_lat_dir_r = '^' + r_ddmm_lat + '\s*(?P<dir>[NS])$'
  re_ddmm_lat_dir_s = '^(?P<dir>-?)' + r_ddmm_lat + '$'

  ' ===== LONGITUDE ===== '
  r_ddmm_lon_max = '(?P<deg>180)(?P<min>00(?:\.(0*))?)'
  re_ddmm_lon_max_dir_l = '^(?P<dir>W)\s*' + r_ddmm_lon_max + '$'
  re_ddmm_lon_max_dir_r = '^' + r_ddmm_lon_max + '\s*(?P<dir>W)$'
  re_ddmm_lon_max_dir_s = '^(?P<dir>-)' + r_ddmm_lon_max + '$'

  r_ddmm_lon = '(?P<deg>(1[0-7]|0\d)\d)'\
    '(?P<min>((?P<maxmin>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?))'
  re_ddmm_lon_dir_l = '^(?P<dir>[WE])\s*' + r_ddmm_lon + '$'
  re_ddmm_lon_dir_r = '^' + r_ddmm_lon + '\s*(?P<dir>[WE])$'
  re_ddmm_lon_dir_s = '^(?P<dir>-?)' + r_ddmm_lon + '$'

  """
   ---------------------------------------------------------------
   RegEx strings for DDMMSS.SS coordinates format, i.e.
   lat:  385733.804N   ;   N793012.00  ;   -393320.3334
   lon: 0951555.739W   ;  E1112201.03  ;  -1023949.9900
  """
  ' ===== LATITUDE ===== '
  r_ddmmss_lat_max = '(?P<deg>90)(?P<min>00)(?P<sec>00(?:\.(0*))?)'
  re_ddmmss_lat_max_dir_l = '^(?P<dir>S)\s*' + r_ddmmss_lat_max + '$'
  re_ddmmss_lat_max_dir_r = '^' + r_ddmmss_lat_max + '\s*(?P<dir>S)$'
  re_ddmmss_lat_max_dir_s = '^(?P<dir>-)' + r_ddmmss_lat_max + '$'

  r_ddmmss_lat = '(?P<deg>[0-8]\d)(?P<min>((?P<maxmin>60)|[0-5]\d))'\
    '(?P<sec>(?(maxmin)00(?:\.(0*))?|'\
    '((?P<maxsec>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?)))'
  re_ddmmss_lat_dir_l = '^(?P<dir>[NS])\s*' + r_ddmmss_lat + '$'
  re_ddmmss_lat_dir_r = '^' + r_ddmmss_lat + '\s*(?P<dir>[NS])$'
  re_ddmmss_lat_dir_s = '^(?P<dir>-?)' + r_ddmmss_lat + '$'

  ' ===== LONGITUDE ===== '
  r_ddmmss_lon_max = '(?P<deg>180)(?P<min>00)(?P<sec>00(?:\.(0*))?)'
  re_ddmmss_lon_max_dir_l = '^(?P<dir>W)\s*' + r_ddmmss_lon_max + '$'
  re_ddmmss_lon_max_dir_r = '^' + r_ddmmss_lon_max + '\s*(?P<dir>W)$'
  re_ddmmss_lon_max_dir_s = '^(?P<dir>-)' + r_ddmmss_lon_max + '$'

  r_ddmmss_lon = '(?P<deg>(1[0-7]|0\d)\d)(?P<min>((?P<maxmin>60)|[0-5]\d))'\
    '(?P<sec>(?(maxmin)00(?:\.(0*))?|((?P<maxsec>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?)))'
  re_ddmmss_lon_dir_l = '^(?P<dir>[WE])\s*' + r_ddmmss_lon + '$'
  re_ddmmss_lon_dir_r = '^' + r_ddmmss_lon + '\s*(?P<dir>[WE])$'
  re_ddmmss_lon_dir_s = '^(?P<dir>-?)' + r_ddmmss_lon + '$'

  """
   ---------------------------------------------------------------
   RegEx strings for DD MM SS coordinates format, i.e.
   lat:  N43°38'19.39"  ;   43°38'19.39"N  ;    43 38 19.39
   lon: W116°14'28.86"  ;  116°14'28.86"W  ;  -116 14 28.86
  """
  ' ===== LATITUDE ===== '
  r_DDMMSS_lat_max = '(?P<deg>90)\s*°?\s*'\
    '(?P<min>00)\s*\'?\s*'\
    '(?P<sec>00(?:\.(0*))?)\s*"?'
  re_DDMMSS_lat_max_dir_l = '^(?P<dir>S)\s*' + r_DDMMSS_lat_max + '$'
  re_DDMMSS_lat_max_dir_r = '^' + r_DDMMSS_lat_max + '\s*(?P<dir>S)$'
  re_DDMMSS_lat_max_dir_s = '^(?P<dir>-)\s*' + r_DDMMSS_lat_max + '$'

  r_DDMMSS_lat = '(?P<deg>[0-8]\d)\s*°?\s*'\
    '(?P<min>((?P<maxmin>60)|[0-5]\d))\s*\'?\s*'\
    '(?P<sec>(?(maxmin)00(?:\.(0*))?|'\
    '((?P<maxsec>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?)))\s*"?'
  re_DDMMSS_lat_dir_l = '^(?P<dir>[NS])\s*' + r_DDMMSS_lat + '$'
  re_DDMMSS_lat_dir_r = '^' + r_DDMMSS_lat + '\s*(?P<dir>[NS])$'
  re_DDMMSS_lat_dir_s = '^(?P<dir>-?)\s*' + r_DDMMSS_lat + '$'

  ' ===== LONGITUDE ===== '
  r_DDMMSS_lon_max = '(?P<deg>180)\s*°?\s*'\
    '(?P<min>00)\s*\'?\s*'\
    '(?P<sec>00(?:\.(0*))?)\s*"?'
  re_DDMMSS_lon_max_dir_l = '^(?P<dir>W)\s*' + r_DDMMSS_lon_max + '$'
  re_DDMMSS_lon_max_dir_r = '^' + r_DDMMSS_lon_max + '\s*(?P<dir>W)$'
  re_DDMMSS_lon_max_dir_s = '^(?P<dir>-)' + r_DDMMSS_lon_max + '$'

  r_DDMMSS_lon = '(?P<deg>(1[0-7]|0\d)\d)'\
    '(?P<min>((?P<maxmin>60)|[0-5]\d))\s*\'?\s*'\
    '(?P<sec>(?(maxmin)00(?:\.(0*))?|'\
    '((?P<maxsec>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?)))\s*"?'
  re_DDMMSS_lon_dir_l = '^(?P<dir>[WE])\s*' + r_DDMMSS_lon + '$'
  re_DDMMSS_lon_dir_r = '^' + r_DDMMSS_lon + '\s*(?P<dir>[WE])$'
  re_DDMMSS_lon_dir_s = '^(?P<dir>-?)' + r_DDMMSS_lon + '$'

  """
   ---------------------------------------------------------------
   RegEx strings for DD MM coordinates format, i.e.
   lat:  N43°38.4539'  ;   43°38.39'N  ;    43 38.39
   lon: W116°14.2186'  ;  116°14.86'W  ;  -116 14.86
  """
  ' ===== LATITUDE ===== '
  r_DDMM_lat_max = '(?P<deg>90)\s*°?\s*(?P<min>00(?:\.(0*))?)\s*\'?'
  re_DDMM_lat_max_dir_l = '^(?P<dir>S)\s*' + r_DDMM_lat_max + '$'
  re_DDMM_lat_max_dir_r = '^' + r_DDMM_lat_max + '\s*(?P<dir>S)$'
  re_DDMM_lat_max_dir_s = '^(?P<dir>-)' + r_DDMM_lat_max + '$'

  r_DDMM_lat = '(?P<deg>[0-8]\d)\s*°?\s*'\
    '(?P<min>((?P<maxmin>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?))\s*\'?'
  re_DDMM_lat_dir_l = '^(?P<dir>[NS])\s*' + r_DDMM_lat + '$'
  re_DDMM_lat_dir_r = '^' + r_DDMM_lat + '\s*(?P<dir>[NS])$'
  re_DDMM_lat_dir_s = '^(?P<dir>-?)' + r_DDMM_lat + '$'

  ' ===== LONGITUDE ===== '
  r_DDMM_lon_max = '(?P<deg>180)\s*°?\s*(?P<min>00(?:\.(0*))?)\s*\'?'
  re_DDMM_lon_max_dir_l = '^(?P<dir>W)\s*' + r_DDMM_lon_max + '$'
  re_DDMM_lon_max_dir_r = '^' + r_DDMM_lon_max + '\s*(?P<dir>W)$'
  re_DDMM_lon_max_dir_s = '^(?P<dir>-)' + r_DDMM_lon_max + '$'

  r_DDMM_lon = '(?P<deg>(1[0-7]|0\d)\d)\s*°?\s*'\
    '(?P<min>((?P<maxmin>60(?:\.(0*))?)|[0-5]\d(?:\.(\d*))?))\s*\'?'
  re_DDMM_lon_dir_l = '^(?P<dir>[WE])\s*' + r_DDMM_lon + '$'
  re_DDMM_lon_dir_r = '^' + r_DDMM_lon + '\s*(?P<dir>[WE])$'
  re_DDMM_lon_dir_s = '^(?P<dir>-?)' + r_DDMM_lon + '$'

  """
   ---------------------------------------------------------------
   A list of regular expression compilers
  """
  __r = {
    'lat': (
      re.compile(re_dec_lat_max, flags=re.IGNORECASE),
      re.compile(re_dec_lat, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lat_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmm_lat_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lat_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMM_lat_max_dir_s, flags=re.IGNORECASE)
    ),
    'lon': (
      re.compile(re_dec_lon_max, flags=re.IGNORECASE),
      re.compile(re_dec_lon, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmmss_lon_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_dir_s, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_ddmm_lon_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMMSS_lon_max_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_dir_s, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_max_dir_l, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_max_dir_r, flags=re.IGNORECASE),
      re.compile(re_DDMM_lon_max_dir_s, flags=re.IGNORECASE)
    )
  }

  @classmethod
  def __getCoord(cls, type, value):
    for r in cls.__r[type]:
      m = r.match(value)
      if m:
        d = m.groupdict()
        found = True
        res = {'deg': 0, 'min': 0, 'sec': 0, 'dir': ""}
        for key in res:
          if key in d:
            res[key] = d[key]
        return cls.convert(res['deg'], res['min'], res['sec'], res['dir'])
    return None

  @classmethod
  def getLatitude(cls, value):
    return cls.__getCoord('lat', value.strip())

  @classmethod
  def getLongitude(cls, value):
    return cls.__getCoord('lon', value.strip())

  '''
  re_coord_delimiter = '^(?P<lat>.+)\s*[,;]\s*(?P<lon>.+)$'
  re_coord_NSWE_left = '^(?P<lat>[^NS]+[NS])\s*(?P<lon>[^WE]+[WE])$'
  re_coord_NSWE_left_rev = '^(?P<lat>.+[NS])\s*(?P<lon>.+[WE])$'
  re_coord_NSWE_right = '^(?P<lat>[^NS]+[NS])\s*(?P<lon>[^WE]+[WE])$'
  re_coord_NSWE_right_rev = '^(?P<lon>[^WE]+[WE])\s*(?P<lat>[^NS]+[NS])$'
  '''

  @classmethod
  def parse(cls, input, aggressive = False):
    #s = input.strip()
    raise NotImplementedError("Not implemented yet")

  @classmethod
  def convert(cls, degrees, minutes, seconds, direction):
    """
     Returns a decimal value of a coordinate, represented in DMS format
     @param degrees: Degrees value of a coordinate
     @param minutes: Minutes of a coordinate
     @param seconds: Seconds of a coordinate
     @param direction: N or S or W or E char 
     @return: Decimal value of a coordinate
    """
    value = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if str.upper(direction) in ("S", "W", "-"):
      value = -value
    return value

  def format(cls, latitude, longitude, fmt):
    raise NotImplementedError("Not implemented yet")

# ! TODO WRITE TEST CASE