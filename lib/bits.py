# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Working with bits utility
@copyright 2012, Maprox LLC
'''

def bitTest(int_type, offset):
    """
     Returns a nonzero result, 2**offset, if the bit at 'offset' is one.
    """
    mask = 1 << offset
    return ((int_type & mask) != 0)

def bitValue(int_type, offset):
    """
     Returns a 1 if the bit at 'offset' is one, else returns 0
    """
    return 1 if bitTest(int_type, offset) else 0

def bitSet(int_type, offset):
    """
     Returns an integer with the bit at 'offset' set to 1.
    """
    mask = 1 << offset
    return (int_type | mask)

def bitClear(int_type, offset):
    """
     Returns an integer with the bit at 'offset' cleared.
    """
    mask = ~(1 << offset)
    return (int_type & mask)

def bitSetValue(int_type, offset, value):
    """
     Set bit value at offset
    """
    if value > 0:
        return bitSet(int_type, offset)
    else:
        return bitClear(int_type, offset)

def bitToggle(int_type, offset):
    """
     Returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0
    """
    mask = 1 << offset
    return (int_type ^ mask)