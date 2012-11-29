# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Finds your external IP address
@copyright 2009-2012, Maprox LLC
'''

import json
from urllib.request import urlopen

def get_ip():
    data = urlopen('http://jsonip.com/').read()
    decoded = json.loads(data.decode())
    return decoded['ip']

if __name__ == '__main__':
    print(get_ip())