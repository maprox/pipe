# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Server configuration module
@copyright 2009-2013, Maprox LLC
'''

import sys
if sys.version_info < (3, 0):
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

from kernel.logger import log
from kernel.commandline import options

conf = ConfigParser()
conf.optionxform = str

try:
    conf.read(options.pipeconf)

    # pipe settings
    conf.redisHost = conf.get("redis", "host")
    conf.redisPort = int(conf.get("redis", "port"))
    conf.redisPassword = conf.get("redis", "password")
    conf.amqpConnection = conf.get("amqp", "connection")
    conf.hostName = conf.get("pipe", "hostname")
    conf.hostIp = conf.get("pipe", "hostip")
    if not conf.hostIp:
        from lib.ip import get_ip
        conf.hostIp = get_ip()
    if not conf.hostName:
        conf.hostName = conf.hostIp
    conf.environment = conf.get("pipe", "environment")
    if not conf.environment:
        conf.environment = 'production'

except Exception as E:
    log.critical("Error reading " + options.pipeconf + ": %s", E)
    exit(1)

try:
    conf.read(options.handlerconf)

    # server's base settings
    if options.port and (options.port != '0'):
        conf.port = int(options.port)
    else:
        conf.port = conf.getint("general", "port")
    conf.socketPacketLength = conf.getint("general", "socketPacketLength")
    conf.pathStorage = conf.get("general", "pathStorage")
    conf.pathTrash = conf.get("general", "pathTrash")

except Exception as E:
    log.critical("Error reading " + options.handlerconf + ": %s", E)
    exit(1)
