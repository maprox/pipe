# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Logger
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/kernel/logger.py $
@version   $Id: logger.py 400 2011-02-20 22:06:46Z sunsay $
'''

import time
import logging
import logging.config
from kernel.commandline import options

# set UTC timezone for logging time
logging.Formatter.converter = time.gmtime

# read logging configuration
logging.config.fileConfig(options.logconf)
log = logging.getLogger();