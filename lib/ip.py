# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Finds your external IP address
@copyright 2009-2013, Maprox LLC
"""

import json
from urllib.request import urlopen

__CachedIP__ = None


def get_ip():
    global __CachedIP__
    if __CachedIP__ is None:
        data = urlopen('http://jsonip.com/').read()
        decoded = json.loads(data.decode())
        __CachedIP__ = decoded['ip']
    return __CachedIP__

if __name__ == '__main__':
    print(get_ip() + ' - from http://jsonip.com/')
    print(get_ip() + ' - from cache')