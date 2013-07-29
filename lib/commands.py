# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Abstract commands
@copyright 2013, Maprox LLC
'''

import json
from kernel.config import conf
from kernel.utils import *

# ---------------------------------------------------------------------------

class AbstractCommand(object):
    """
     Abstract protocol command
    """
    alias = None
    """ Command alias """

    _commandData = None
    """ Command initial data """

    def __init__(self, params = None, commandData = None):
        """
         Initialize command with specific params
         @param params: dict
         @return:
        """
        self._commandData = commandData
        self.setParams(params)

    def setParams(self, params):
        """
         Set command params if needed.
         Override in child classes.
         @param params: dict
         @return:
        """
        return self

    def getData(self, transport = "tcp"):
        """
         Returns command data array accordingly to the transport
         @param transport: str
         @return: list of dicts
        """
        return []

# ---------------------------------------------------------------------------

class AbstractCommandConfigure(AbstractCommand):
    """
     Abstract protocol configuration command
    """

    hostNameNotSupported = False
    """ False if protocol doesn't support dns hostname (only ip-address) """

    _initiationConfig = None

    def setParams(self, params):
        """
         Set command params if needed.
         @param params: dict
         @return:
        """
        self._initiationConfig = self.getInitiationConfig(params)

    def getInitiationConfig(self, rawConfig):
        """
         Returns prepared initiation data object
         @param rawConfig: input json string or dict
         @return: dict (json) object
        """
        data = rawConfig
        if isinstance(data, str): data = json.loads(data)
        dictSetItemIfNotSet(data, 'identifier', '')
        # host and port part of input
        dictSetItemIfNotSet(data, 'port', str(conf.port))
        dictSetItemIfNotSet(data, 'host', conf.hostIp\
            if self.hostNameNotSupported else conf.hostName)
        # device part of input
        dictSetItemIfNotSet(data, 'device', {})
        dictSetItemIfNotSet(data['device'], 'login', '')
        dictSetItemIfNotSet(data['device'], 'password', '')
        # gprs part of input
        dictSetItemIfNotSet(data, 'gprs', {})
        dictSetItemIfNotSet(data['gprs'], 'apn', '')
        dictSetItemIfNotSet(data['gprs'], 'username', '')
        dictSetItemIfNotSet(data['gprs'], 'password', '')
        return data


import inspect
import sys

def getCommandClassByAlias(alias, module = __name__):
    """
     Returns command answer's class by its number
     @param number: int Number of the command
     @return: Command class
    """
    for name, cls in inspect.getmembers(sys.modules[module]):
        if inspect.isclass(cls) and issubclass(cls, AbstractCommand):
            if cls.alias == alias:
                return cls
    return None
