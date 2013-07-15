# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Util functions
@copyright 2013, Maprox LLC
'''

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

