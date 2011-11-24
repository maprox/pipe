# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Protocol handlers list
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/lib/listeners/list.py $
@version   $Id: list.py 403 2011-02-24 13:26:07Z sunsay $
'''

from kernel.logger import log
from kernel.config import conf
from kernel.pipe import Manager

# Loads modules
handlersList = list()
for protocol in conf.protocols:
  name = "lib.handlers." + protocol
  try:
    pkg = __import__(name, globals(), locals(), ['Handler'])
    if (hasattr(pkg, 'Handler')):
      cls = getattr(pkg, 'Handler')
      handlersList.append(cls)
      log.info("Protocol is loaded: " + cls.__doc__)
    else:
      log.error("Class 'Handler' in not found in module %s", name)
  except Exception as E:
    log.error("Protocol '%s' loading error: %s", name, E)
    continue
