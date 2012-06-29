# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Logger
@copyright 2009-2012, Maprox LLC
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