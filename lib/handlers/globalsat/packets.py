# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Globalsat packets
@copyright 2013, Maprox LLC
"""

import re

def getChecksum(data):
    """
     Returns the data checksum
     @param data: data string
     @return: hex string checksum
    """
    checksum = 0
    for c in data:
        checksum ^= ord(c)
    hex_checksum = "%02X" % checksum
    return hex_checksum

def addChecksum(data, fmt = "{d}*{c}!"):
    """
     Adds checksum to a data string
     @param data: data string
     @return: data, containing checksum part
    """
    return str.format(fmt, d = data, c = getChecksum(data))

def truncateChecksum(value):
    """
     Truncates checksum part from value string
     @param value: value string
     @return: truncated string without checksum part
    """
    return re.sub('\*(\w{1,4})!', '', value)