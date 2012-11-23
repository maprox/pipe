# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Command line reading module
@copyright 2009-2012, Maprox LLC
'''

from optparse import OptionParser

options = OptionParser()
options.add_option(
  "-p",
  "--pipeconf",
  dest="pipeconf",
  help="path to the pipe configuration file",
  metavar="PathToPipeConf",
  default="../conf/pipe.conf"
)

(options, args) = options.parse_args()