# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Command line reading module
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
'''

from optparse import OptionParser

options = OptionParser()
options.add_option(
   "-l",
   "--logconf",
   dest="logconf",
   help="path to the log config file",
   metavar="PathToLogConf",
   default="conf/log.conf")

options.add_option(
   "-s",
   "--servconf",
   dest="servconf",
   help="path to the server configuration file",
   metavar="PathToServConf",
   default="conf/serv.conf")

options.add_option(
   "-p",
   "--pipeconf",
   dest="pipeconf",
   help="path to the pipe configuration file",
   metavar="PathToPipeConf",
   default="conf/pipe.conf")

options.add_option(
   "--pipe_server_mask",
   dest="pipe_server_mask",
   help="pipe process identifier",
   metavar="ProcessId",
   default="000")

options.add_option(
   "--port",
   dest="port",
   help="pipe process identifier",
   metavar="ProcessPort",
   default=False)

(options, args) = options.parse_args()
