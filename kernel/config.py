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
    conf.pipeKey = conf.get("pipe", "key")
    conf.pipeSetUrl = conf.get("pipe", "urlset")
    conf.pipeFinishUrl = conf.get("pipe", "urlfinish")
    conf.pipeRequestUrl = conf.get("pipe", "urlrequest")
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

except Exception as E:
    log.critical("Error reading " + options.pipeconf + ": %s", E)
    exit(1)

try:
    conf.read(options.handlerconf)

    # server's base settings
    if options.port:
        conf.port = int(options.port)
    else:
        conf.port = conf.getint("general", "port")
    conf.socketTimeout = conf.getint("general", "socketTimeout")
    conf.socketPacketLength = conf.getint("general", "socketPacketLength")
    conf.socketDataMaxLength = conf.getint("general", "socketDataMaxLength")
    conf.setDaemon = conf.getboolean("general", "setDaemon")
    conf.pathStorage = conf.get("general", "pathStorage")
    conf.pathTrash = conf.get("general", "pathTrash")

except Exception as E:
    log.critical("Error reading " + options.handlerconf + ": %s", E)
    exit(1)
