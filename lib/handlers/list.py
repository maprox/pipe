# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Protocol handlers list
@copyright 2009-2011, Maprox LLC
'''

from kernel.logger import log
from kernel.config import conf

# Load modules
HandlerClass = None
handlerName = conf.get('settings', 'handler')
handlerClassPath = "lib.handlers." + handlerName
try:
    pkg = __import__(handlerClassPath, globals(), locals(), ['Handler'])
    if (hasattr(pkg, 'Handler')):
        HandlerClass = getattr(pkg, 'Handler')
        HandlerClass.initAmqpThread(handlerName)
        log.info("Protocol is loaded: " + HandlerClass.__doc__)
    else:
        log.error("Class 'Handler' in not found in module %s",
            handlerClassPath)
except Exception as E:
    log.error("Protocol '%s' loading error: %s", handlerClassPath, E)
