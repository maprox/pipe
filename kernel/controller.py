# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Controller
@copyright 2009-2012, Maprox LLC
'''

from kernel.logger import log
from kernel.dbmanager import db
from lib.handlers.list import handlersList

# ===========================================================================
class Controller(object):
    '''
     Pipe-server controller
    '''

    __handlerTranslation = {
     'tr600': 'globalsat.tr-600',
     'tr203': 'globalsat.tr-203',
     'tr206': 'globalsat.tr-206',
     'naviset': 'naviset.gt-20',
     'galileo': 'galileo.firmware-0119'
    }

    def __init__(self):
        """
         Controller constructor
        """
        log.debug('Controller::__init__')

    def run(self):
        """
         Starting check of execution commands
        """
        log.debug('Controller::run()')
        # try:
        commands = db.getController().getCommands()
        for command in commands:
            handler = 'lib.handlers.' \
              + self.__handlerTranslation[command['handler']]
            for HandlerClass in handlersList:
                if HandlerClass.__module__ == handler:
                    handler = HandlerClass(False, False)
                    handler.uid = command['uid']
                    function_name = 'processCommand' \
                      + command['action'][0].upper() \
                      + command['action'][1:]
                    log.debug('Command is: ' + function_name)
                    function = getattr(handler, function_name)
                    if 'value' in command:
                        function(command['id'], command['value'])
                    else:
                        function(command['id'], None)
        #  except Exception as E:
        #    log.critical(E)
