# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Server configuration module
@copyright 2009-2016, Maprox LLC
"""

import os
import sys

if sys.version_info < (3, 0):
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

from kernel.logger import log
from kernel.options import options

conf = ConfigParser()
conf.optionxform = str

try:
    conf.read(options.pipeconf)

    # pipe settings
    conf.socketPacketLength = conf.getint("pipe", "socketPacketLength")
    conf.environment = os.getenv(
        "PIPE_ENVIRONMENT", conf.get("pipe", "environment"))
    conf.hostName = os.getenv(
        "PIPE_HOSTNAME", conf.get("pipe", "hostname"))
    conf.hostIp = os.getenv(
        "PIPE_HOSTIP", conf.get("pipe", "hostip"))

    # redis settings
    conf.redisHost = os.getenv(
        "REDIS_HOST", conf.get("redis", "host"))
    conf.redisPort = int(os.getenv(
        "REDIS_PORT", conf.get("redis", "port")))
    conf.redisPassword = os.getenv(
        "REDIS_PASS", conf.get("redis", "password"))

    # amqp settings
    conf.amqpConnection = os.getenv(
        "AMQP_CONNECTION", conf.get("amqp", "connection"))

    # default settings if not set up previously
    if not conf.hostIp:
        from lib.ip import get_ip
        conf.hostIp = get_ip()

    if not conf.hostName:
        conf.hostName = conf.hostIp

    if not conf.environment:
        conf.environment = 'production'

    if not options.handler:
        options.handler = os.getenv('PIPE_HANDLER')

    if options.handler:
        options.handlerconf = 'conf/handlers/' + options.handler + '.conf'

except Exception as E:
    log.critical("Error reading " + options.pipeconf + ": %s", E)
    exit(1)

try:
    conf.handler = options.handler
    if options.handlerconf:
        conf.read(options.handlerconf)
        if not conf.handler:
            # deprecated loading of handler alias
            conf.handler = conf.get('settings', 'handler')

    # server's base settings
    if options.port:
        conf.port = int(options.port)
    else:
        conf.port = int(os.getenv('PIPE_PORT', 0))

    if not conf.port and options.handlerconf:
        conf.port = conf.getint("general", "port")

except Exception as E:
    log.critical("Error reading " + options.handlerconf + ": %s", E)
    exit(1)
