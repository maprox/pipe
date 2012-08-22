# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Abstract class for all implemented protocols
@copyright 2009-2012, Maprox LLC
'''

from datetime import datetime
import re
import json
import base64
from urllib.parse import urlencode
from kernel.logger import log
from kernel.config import conf
from kernel.database import db
from lib.storage import storage
from urllib.request import urlopen

class AbstractHandler(object):
  """ Abstract class for all implemented protocols """

  default_options = {}

  transmissionEndSymbol = "\n"
  """ Symbol which marks end of transmission for PHP """

  uid = False
  """ Uid of currently connected device """

  re_request = re.compile('^OBS,request\((?P<data>.+)\)$')
  re_success = re.compile('^OBS,request\(.*success.*\)$')

  def __init__(self, store, clientThread):
    """
     Constructor of Listener.
     @param store: kernel.pipe.Manager instance
     @param clientThread: Instance of kernel.server.ClientThread
    """
    log.debug('%s::__init__()', self.__class__)
    self.__store = store
    self.__thread = clientThread

  def getStore(self):
    """ Returns store object """
    return self.__store

  def getThread(self):
    """ Returns clientThread object """
    return self.__thread

  def dispatch(self):
    """
      Data processing method (after validation) from the device:
      clientThread thread of the socket;
    """
    log.debug('%s::dispatch()', self.__class__)
    self.prepare()
    return self

  def prepare(self):
    """
     Preparing for data transfer.
     Can be overridden in child classes
    """
    return self

  def processData(self, data):
    """
     Processing of data from socket / storage.
     Must be overridden in child classes
     @param data: Data from socket
    """

    if self.uid:

      commands = self.getCommands()
      self.processRequest(commands)

      current_db = db.get(self.uid)
      if current_db.isReadReady():
        send = {}
        config = self.translateConfig(current_db.getRead())
        send['config'] = json.dumps(config, separators=(',',':'))
        connection = urlopen(conf.pipeSetUrl + urlencode(send))
        log.debug('Sending config: ' + conf.pipeSetUrl + urlencode(send))
        answer = connection.read()
        log.debug('Config answered: ' + answer.decode())
        result = self.re_success.search(answer.decode(), 0)
        if result:
          current_db.deleteRead()

    return self

  def getCommands(self):
    connection = urlopen(conf.pipeGetUrl + 'uid=' + self.uid)
    answer = connection.read()
    return answer.decode()

  def processRequest(self, data):
    """
     Processing of observer request from socket
     @param data: request
    """

    position = 0

    log.debug("Search match in '" + data + "'")
    m = self.re_request.search(data, position)
    if m:
      log.debug("Request match found.")
      data = m.groupdict()['data']
      data = json.loads(data)

      if data:
        for command in data:
          function_name = 'processCommand' + command['cmd'].capitalize()
          function = getattr(self, function_name)
          if 'data' in command:
            function(command['data'])
          else:
            function(None)

      self.send(self.transmissionEndSymbol.encode())

    else:
      log.error("Incorrect request format")

    return self

  def recv(self):
    """
     Receiving data from socket
     @param the_socket: Instance of a socket object
     @return: String representation of data
    """
    sock = self.getThread().request
    sock.settimeout(conf.socketTimeout)
    total_data = []
    while True:
      try:
        data = sock.recv(conf.socketPacketLength)
      except Exception as E:
        break
      log.debug('Data chunk = %s', data)
      if not data: break
      total_data.append(data)
      """ I don't know why [if not data: break] is not working, so
          let's do break here """
      if len(data) < conf.socketPacketLength: break
    log.debug('Total data = %s', total_data)
    return b''.join(total_data)

  def send(self, data):
    """
     Sends data to a socket
     @param data: data
    """
    sock = self.getThread().request
    sock.send(data)
    return self

  def store(self, packets):
    """
     Sends a list of packets to store
     @param packets: A list of packets
     @return: Instance of lib.falcon.answer.FalconAnswer
    """
    result = self.getStore().send(packets)
    if (result.isSuccess()):
      log.debug('%s::store() ... OK', self.__class__)
    else:
      # ? Error messages should be converted into readable format
      log.error('%s::store():\n %s', self.__class__, result.getErrorsList())
      # send data to storage on error to save packets
      storage.save(packets)
    return result

  def translate(self, data):
    """
     Translate gps-tracker data to observer pipe format
     @param data: dict() data from gps-tracker
    """
    raise NotImplementedError("Not implemented Handler::translate() method")

  def translateConfig(self, data):
    """
     Translate gps-tracker config data to observer format
     @param data: {string[]} data from gps-tracker
    """
    raise NotImplementedError("Not implemented Handler::translateConfig() method")

  def sendImages(self, images):
    """
     Sends image to the observer
     @param images: dict() of binary data like {'camera1': b'....'}
    """
    if not self.uid:
      log.error('Cant send an image - self.uid is not defined!')
      return
    imageslist = []
    for image in images:
      image['content'] = base64.b64encode(image['content']).decode()
      imageslist.append(image)
    observerPacket = {
      'uid': self.uid,
      'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
      'images': imageslist
    }
    result = self.store(observerPacket)
    if (result.isSuccess()):
      log.info('%s::sendImages(): Images have been sent.', self.__class__)
    else:
      print(result.getErrorsList())
      # ? Error messages should be converted into readable format
      log.error('%s::sendImages():\n %s',
        self.__class__, result.getErrorsList())

