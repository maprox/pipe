# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Class for working with pipe-controller 
@copyright 2009-2012, Maprox LLC
'''

class Store(object):
  """
   Abstract class defining storage for device packets
  """

  def __init__(self):
    """
     Constructor
    """
    pass

  def send(self, obj):
    """
     Sending data to the store
     @param obj: (list | dict) Packet object(s)
    """
    return FalconAnswer()