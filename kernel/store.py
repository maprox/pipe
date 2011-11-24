# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Class for working with pipe-controller 
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL$
@version   $Id$
'''

class Store(object):
  """ Abstract class defining storage for device packets"""

  def __init__(self):
    """ Constructor """
    pass

  def send(self, obj):
    """
     Sending data to the store
     @param obj: (list | dict) Packet object(s)
    """
    return FalconAnswer()