# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Class of storage for protocol handlers (Files I/O)
@copyright 2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL$
@version   $Id$
'''

import re
import os
import base64
import shutil
import glob
import copy

from kernel.logger import log
from kernel.config import conf

class Storage(object):
  """
   Class of storage for protocol handlers (Files I/O).
   Used when there is an error during sending data to the pipe controller.
   Stores protocol data in files, wich then can be restored when
   error on pipe controller fixed
  """

  filePostfix = '.storage'
  re_uid = re.compile('\w+')
  re_port = re.compile('\d+')
  __path = os.path.join(conf.pathStorage, str(conf.port))

  def __init__(self):
    """
     Storage constructor
    """
    log.debug('%s::__init__()', self.__class__)
    os.makedirs(self.__path, 0o777, True)

  def getStorageFileName(self, uid):
    """
     Returns storage filename.
     If uid doesn't match to the regular expression \w+ eq. [A-Za-z0-9_] then
     we take base64 encoded string of uid as a file name.
     @param uid: Device identifier
    """
    if (self.re_uid.match(uid)):
      storageFileName = uid
    else:
      storageFileName = base64.b64encode(uid.encode()).decode()
    return os.path.join(self.__path, storageFileName + self.filePostfix)

  def save(self, packets):
    """
     Save protocol data into storage
     @param packets: list of packets to save into storage
    """
    for packet in packets:
      self.saveByUid(packet['uid'], packet['__rawdata'])

  def saveByUid(self, uid, data):
    """
     Save protocol data into storage
     @param uid: Device unqiue identifier
     @param data: Protocol data
    """
    log.debug('Storage::saveByUid(). %s', uid)
    try:
      f = open(self.getStorageFileName(uid), 'a')
      try:
        f.write(data + '\n')
      finally:
        f.close()
    except Exception as E:
      log.error(E)

  def locate(self, pattern, root=os.curdir):
    """
     Locate all files matching supplied filename pattern in and below
     supplied root directory.
    """
    # for path, dirs, files in os.walk(os.path.abspath(root)):
    files = os.listdir(os.path.abspath(root))
    for filename in fnmatch.filter(files, pattern):
      yield filename

  def load(self):
    """
     Returns all existed data in storage
     @return (list) Storage data
    """
    list = []
    for dirPort in glob.glob(os.path.join(conf.pathStorage, '*')):
      basename = os.path.basename(dirPort)
      if os.path.isdir(dirPort) and self.re_port.match(basename):
        record = {}
        record['port'] = basename
        record['data'] = []
        for storageFileName in glob.glob(
            os.path.join(dirPort, '*' + self.filePostfix)):
          if (os.path.isfile(storageFileName)):
            filedata = {}
            f = open(storageFileName, 'r')
            try:
              filedata['name'] = os.path.basename(storageFileName),
              filedata['contents'] = f.read()
            finally:
              f.close()
            record['data'].append(filedata)
        list.append(record)
    return list

  def loadByUid(self, uid):
    """
     Returns saved protocol data by specified uid
     @param uid: Device unqiue identifier
     @return (str) Storage file data
    """
    log.debug('Storage::loadByUid(). %s', uid)
    data = ''
    try:
      storageFileName = self.getStorageFileName(uid);
      if (os.path.isfile(storageFileName)):
        f = open(storageFileName, 'r')
        try:
          data = f.read()
        finally:
          f.close()
    except Exception as E:
      log.error(E)
    return data

  def clear(self):
    """
     Clear storage.
     @warning By calling this function you delete folder at conf.pathStorage
    """
    log.debug('Storage::clear()')
    shutil.rmtree(conf.pathStorage)

storage = Storage()