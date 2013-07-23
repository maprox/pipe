# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Util functions
@copyright 2013, Maprox LLC
'''

from struct import pack

# ---------------------------------------------------------------------------

def dictCheckItem(data, name, value):
    """
     Checks if "name" is in "data" dict. If yes, returns data[name],
     if no, returns default "value"
     @param data: input dict
     @param name: key of dict to check
     @param value: value of dict item at key "name"
    """
    if not data:
        return value
    elif name not in data:
        return value
    else:
        return data[name]

def dictSetItemIfNotSet(data, name, value):
    """
     Checks if "name" is in "data" dict. If not, creates it with "value"
     @param data: input dict
     @param name: key of dict to check
     @param value: value of dict item at key "name"
    """
    if name not in data: data[name] = value

def packString(value):
    """
     Packs a string into bytes variable as [L][VALUE], where [L] is a
     one-byte length of the string and [VALUE] is encoded string
     @param value: input str
     @return: output bytes
    """
    strLen = len(value)
    result = pack('>B', strLen)
    if strLen > 0:
        result += value.encode()
    return result