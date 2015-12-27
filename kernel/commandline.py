# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Command line reading module
@copyright 2009-2012, Maprox LLC
'''

from optparse import OptionParser
options = OptionParser()
options.add_option(
    "-l",
    "--logconf",
    dest="logconf",
    help="Path to the log config file",
    metavar="PathToLogConf",
    default="conf/logs/default.conf"
)

options.add_option(
    "-c",
    "--handlerconf",
    dest="handlerconf",
    help="Path to the protocol handler configuration file",
    metavar="PathToHandlerConf",
    default="conf/handlers/default.conf"
)

options.add_option(
    "-s",
    "--pipeconf",
    dest="pipeconf",
    help="Path to the pipe configuration file",
    metavar="PathToPipeConf",
    default="conf/pipe.conf"
)

options.add_option(
    "-m",
    "--pipe_process_mask",
    dest="mask",
    help="Pipe process identifier (deprecated)",
    metavar="ProcessId",
    default="000"
)

options.add_option(
    "-p",
    "--port",
    dest="port",
    help="Pipe handler port",
    metavar="Port",
    default=False
)

(options, args) = options.parse_args()
