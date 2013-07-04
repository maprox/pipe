# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Protocol handlers list
@copyright 2009-2011, Maprox LLC
'''

from kernel.logger import log
from kernel.config import conf

# Load modules
handlersList = list()
for protocol in conf.protocols:
    name = "lib.handlers." + protocol
    try:
        pkg = __import__(name, globals(), locals(), ['Handler'])
        if (hasattr(pkg, 'Handler')):
            cls = getattr(pkg, 'Handler')
            cls.initAmqpThread(conf.get("protocols", protocol))
            handlersList.append(cls)
            log.info("Protocol is loaded: " + cls.__doc__)
        else:
            log.error("Class 'Handler' in not found in module %s", name)
    except Exception as E:
        log.error("Protocol '%s' loading error: %s", name, E)
        continue
