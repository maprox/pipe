# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Модуль конфигурации сервера
@copyright 2009-2011 © Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''

import configparser
from kernel.logger import log
from kernel.commandline import options

conf = configparser.ConfigParser()
try:
  conf.read(options.servconf);

  # общие настройки сервера
  if options.port:
    conf.port = int(options.port)
  else:
    conf.port = conf.getint("general", "port")
  conf.socketPacketLength = conf.getint("general", "socketPacketLength")
  conf.socketDataMaxLength = conf.getint("general", "socketDataMaxLength")
  conf.setDaemon = conf.getboolean("general", "setDaemon")
  conf.pathStorage = conf.get("general", "pathStorage")
  conf.pathTrash = conf.get("general", "pathTrash")
  conf.protocols = []
  for item in conf.items('protocols'):
    conf.protocols.append(item[0])
#  conf.protocols = list(conf.items('protocols'))

except Exception as E:
  log.critical("Error reading " + options.servconf + ": " + E.message)
  exit(1)

try:
  conf.read(options.pipeconf);

  # настройки pipe
  conf.pipeKey = conf.get("pipe", "key")
  conf.pipeSetUrl = conf.get("pipe", "urlset")
  conf.pipeGetUrl = conf.get("pipe", "urlget")
  conf.pipeConfigUrl = conf.get("pipe", "urlconfig")

except Exception as E:
  log.critical("Error reading " + options.pipeconf + ": " + E.message)
  exit(1)
