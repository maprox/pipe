# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Class of storage for protocol handlers (Files I/O)
@copyright 2012, Maprox LLC
'''

import re
import os
import base64
import shutil
import time
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
        try:
            os.makedirs(self.__path, 0o777, True)
        except:
            pass

    def getStorageFileName(self, uid):
        """
         Returns storage filename.
         If uid doesn't match to the regular expression \w+
         eq. [A-Za-z0-9_] then we take base64 encoded
         string of uid as a file name.
         @param uid: Device identifier
        """
        if (self.re_uid.match(uid)):
            storageFileName = uid
        else:
            storageFileName = base64.b64encode(uid.encode()).decode()

        if not os.path.isdir(self.__path):
            try:
                os.makedirs(self.__path, 0o777, True)
            except:
                pass

        return os.path.join(self.__path, storageFileName + self.filePostfix)

    def save(self, uid, data):
        """
         Save protocol data into storage
         @param uid: device identifier
         @param data: data to save to the storage
        """
        self.saveByUid(uid, data)

    def saveByUid(self, uid, data):
        """
         Save protocol data into storage
         @param uid: Device unqiue identifier
         @param data: Protocol data
        """
        log.debug('Storage::saveByUid(). %s', uid)
        try:
            with open(self.getStorageFileName(uid), 'ab') as f:
                f.write(data)
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
                        f_data = {}
                        with open(storageFileName, 'rb') as f:
                            f_data['name'] = os.path.basename(storageFileName)
                            f_data['contents'] = f.read()
                        record['data'].append(f_data)
                list.append(record)
        return list

    def delete(self, item, port, timestamp):
        """
         Removes item from storage, puts in trash
         @param item: Item we want to remove
         @param port: Device port
         @param timestamp: Start timestamp
        """
        try:
            uidName = item['name']
            filename = os.path.join(conf.pathStorage, port, uidName)
            newName = os.path.join(conf.pathTrash, timestamp, port, uidName)
            log.info('Delete data for %s', uidName)
            log.info('fileName = %s, newName = %s', filename, newName)
            newDir = os.path.dirname(newName)
            log.debug(newDir)
            if not os.path.exists(newDir):
                os.makedirs(newDir)
            os.rename(filename, newName)
        except Exception as E:
            log.error(E)

    def loadByUid(self, uid):
        """
         Returns saved protocol data by specified uid
         @param uid: Device unqiue identifier
         @return (str) Storage file data
        """
        log.debug('Storage::loadByUid(). %s', uid)
        data = b''
        try:
            storageFileName = self.getStorageFileName(uid);
            if (os.path.isfile(storageFileName)):
                with open(storageFileName, 'rb') as f:
                    data = f.read()
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
