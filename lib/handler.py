# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Abstract class for all implemented protocols
@copyright 2009-2013, Maprox LLC
"""

from datetime import datetime
import re
import json
import base64
from urllib.parse import urlencode
from kernel.logger import log
from kernel.config import conf
from kernel.dbmanager import db
from lib.storage import storage
from urllib.request import urlopen
from lib.broker import broker
import http.client

class AbstractHandler(object):
    """
     Abstract class for all implemented protocols
    """
    _packetsFactory = None # packets factory link
    _commandsFactory = None # commands factory link

    _buffer = None # buffer of the current dispatch loop (for storage save)
    _uid = None # identifier of currently connected device

    def __init__(self, store, clientThread):
        """
         Constructor of Listener.
         @param store: kernel.pipe.Manager instance
         @param clientThread: Instance of kernel.server.ClientThread
        """
        log.debug('%s::__init__()', self.__class__)
        self.__store = store
        self.__thread = clientThread
        self.initialization()

    def __del__(self):
        """
         Destructor of Listener
         @return:
        """
        self.finalization()

    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        broker.handlerInitialize(self)

    def finalization(self):
        """
         Finalization of the handler.
         Free allocated resources.
         @return:
        """
        broker.handlerFinalize(self)

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value
        broker.handlerUpdate(self)

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
        buffer = self.recv()
        while len(buffer) > 0:
            self.processData(buffer)
            buffer = self.recv()
        log.debug('%s::dispatch() - EXIT (empty buffer?)', self.__class__)

    def needProcessCommands(self):
        """
         Returns false if we can not process commands
         @return: boolean
        """
        return self.uid

    def processData(self, data):
        """
         Processing of data from socket / storage.
         Must be overridden in child classes
         @param data: Data from socket
        """
        if self._packetsFactory:
            try:
                protocolPackets = (
                    self._packetsFactory.getPacketsFromBuffer(data)
                )
                for protocolPacket in protocolPackets:
                    self.processProtocolPacket(protocolPacket)
            except Exception as E:
                log.error("processData error: %s", E)

        if not self.needProcessCommands(): return self

        self.processCommands()

        # try is now silently excepting all the errors
        # to avoid connection errors during testing
        try:
            current_db = db.get(self.uid)
            self.processRequest(current_db.getCommands())

            current_db = db.get(self.uid)
            if current_db.isSettingsReady():
                send = {}
                config = self.translateConfig(current_db.getSettings())
                send['config'] = json.dumps(config, separators=(',',':'))
                send['id_action'] = current_db.getSettingsTaskId()
                log.debug('Sending config: ' + 
                    conf.pipeSetUrl + urlencode(send))
                connection = urlopen(conf.pipeSetUrl, urlencode(send).encode())
                answer = connection.read()
                log.debug('Config answered: ' + answer.decode())
                current_db.deleteSettings()
        except Exception as E:
            log.error(E)
        return self

    def processProtocolPacket(self, protocolPacket):
        """
         Process protocol packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Protocol packet
        """
        pass

    def processRequest(self, data):
        """
         Processing of observer request from socket
         @param data: request
        """
        for command in data:
            function_name = 'processCommand' \
              + command['action'][0].upper() \
              + command['action'][1:]
            log.debug('Command is: ' + function_name)
            function = getattr(self, function_name)
            if 'value' in command:
                function(command['id'], command['value'])
            else:
                function(command['id'], None)
        return self

    def getTaskData(self, task, data = None):
        """
         Return close task data
         @param task: Task identifier
         @param data: Result data to send. [Optional]
         @return dict
        """
        message = { "id_action": task }
        if data is not None:
            content = data
            if isinstance(data, str):
                content = [{
                    "message": data
                }]
            message['data'] = json.dumps(content)
        return message

    def processCloseTask(self, task, data = None):
        """
         Close task
         @param task: Task identifier
         @param data: Result data to send. [Optional]
        """
        message = self.getTaskData(task, data)
        params = urlencode(message)
        log.debug('Close task: ' + conf.pipeFinishUrl + params)

        urlParts = re.search('//(.+?)(/.+)', conf.pipeFinishUrl)
        restHost = urlParts.group(1)
        restPath = urlParts.group(2)

        conn = http.client.HTTPConnection(restHost, 80)
        conn.request("POST", restPath, params, {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        })
        conn.getresponse()
        return self

    def recv(self):
        """
         Receiving data from socket
         @return: String representation of data
        """

        sock = self.getThread().request
        sock.settimeout(conf.socketTimeout)
        total_data = []
        while True:
            try:
                data = sock.recv(conf.socketPacketLength)
            except Exception as E:
                log.debug(E)
                break
            log.debug('Data chunk = %s', data)
            if not data: break
            total_data.append(data)
            # I don't know why [if not data: break] is not working,
            # so let's do break here
            if len(data) < conf.socketPacketLength: break
        log.debug('Total data = %s', total_data)

        return b''.join(total_data)

    def send(self, data):
        """
         Sends data to a socket
         @param data: data
        """
        thread = self.getThread()
        if thread:
            sock = thread.request
            sock.send(data)
        else:
            log.error("Handler thread is not found!")
        return self

    def store(self, packets):
        """
         Sends a list of packets to store
         @param packets: A list of packets
         @return: Instance of lib.falcon.answer.FalconAnswer
        """
        result = self.getStore().send(packets)
        if result.isSuccess():
            log.debug('%s::store() ... OK', self.__class__)
        else:
            errorsList = result.getErrorsList()
            log.error('%s::store():\n %s', self.__class__, errorsList)
            savePackets = True
            if len(errorsList) > 0:
                e = errorsList[0]
                if 'params' in e:
                    params = e['params']
                    if len(params) > 1:
                        savePackets = (params[1] != 404)
            if savePackets:
                # send data to storage on error to save packets
                storage.save(self.uid if self.uid else 'unknown',
                    self._buffer)
        return result

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        raise NotImplementedError(
            "Not implemented Handler::translate() method")

    def translateConfig(self, data):
        """
         Translate gps-tracker config data to observer format
         @param data: {string[]} data from gps-tracker
        """
        raise NotImplementedError(
            "Not implemented Handler::translateConfig() method")

    def sendImages(self, images):
        """
         Sends image to the observer
         @param images: dict() of binary data like {'camera1': b'....'}
        """
        if not self.uid:
            log.error('Cant send an image - self.uid is not defined!')
            return
        imagesList = []
        for image in images:
            image['content'] = base64.b64encode(image['content']).decode()
            imagesList.append(image)
        observerPacket = {
          'uid': self.uid,
          'time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
          'images': imagesList
        }
        result = self.store(observerPacket)
        if result.isSuccess():
            log.info('%s::sendImages(): Images have been sent.',
              self.__class__)
        else:
            # ? Error messages should be converted into readable format
            log.error('%s::sendImages():\n %s',
              self.__class__, result.getErrorsList())

    def processCommandProcessSms(self, task, data):
        """
         Processing of input sms-message
         @param task: id task
         @param data: data string
        """
        self.processCloseTask(task)
        return self

    def setPacketSensors(self, packet, sensor):
        """
         Makes a copy of some packet data into sensor
         @param sensor: dict
         @param packet: dict
         @return: self
        """
        if (packet and sensor and
            isinstance(packet, dict) and
            isinstance(sensor, dict)):
            for key in ['latitude', 'longitude',
                        'altitude', 'speed',
                        'hdop', 'azimuth']:
                if key in packet:
                    sensor[key] = packet[key]
            packet['sensors'] = sensor.copy()
        return self

    def getConfigOption(self, key, defaultValue = None):
        """
         Returns configuration option by its key
         @param key: Configuration key
         @param defaultValue: Default value if key is not found
         @return: mixed
        """
        if conf.has_section('settings'):
            section = conf['settings']
            return section.get(key, defaultValue)
        return defaultValue

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        log.error('processCommandReadSettings NOT IMPLEMENTED')
        return self.processCloseTask(task, None)

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        log.error('processCommandSetOption NOT IMPLEMENTED')
        return self.processCloseTask(task, None)


    def processCommands(self):
        """
         Processing AMQP commands for current device
        """
        try:
            if not self._commandsFactory:
                raise Exception("_commandsFactory is not defined!")
            commands = broker.getCommands(self.uid)
            if commands:
                log.debug("Received commands are: %s" % commands)
                self.processCommand(commands)
        except Exception as E:
            log.error(E)

    def processCommand(self, command):
        """
         Processing AMQP command
         @param command: command
        """
        if not command:
            log.error("Empty command description!")
            return

        if (not self.uid) and ('uid' in command):
            self.uid = command['uid']

        log.debug("Processing AMQP command: %s " % command)
        try:
            if not self._commandsFactory:
                raise Exception("_commandsFactory is not defined!")
            commandName = command["command"]
            commandInstance = self._commandsFactory.getInstance(command)
            if commandInstance:
                log.debug("Command class is %s: " % commandInstance.__class__)
                self.sendCommand(commandInstance, command)
            else:
                broker.sendAmqpError(self.uid, "Command is not supported")
                log.error("No command with name %s" % commandName)
        except Exception as E:
            log.error("Send command error is %s" % E)

    def sendCommand(self, command, initialParameters = None):
        """
         Sends command to the handler
         @param command: AbstractCommand instance
         @param initialParameters: dict Initial command parameters
        """
        if not initialParameters:
            raise Exception("Empty initial parameters!")

        config = {}
        if "config" in initialParameters:
            config = initialParameters["config"]
        transport = initialParameters["transport"]

        commandData = command.getData(transport) or []
        if not isinstance(commandData, list):
            commandData = [{"message": commandData}]

        for item in commandData:
            if not isinstance(item, dict):
                item = {"message": item}
            buffer = item["message"]
            if transport == "tcp":
                self.send(buffer)
            elif transport == "sms":
                data = {
                    'type': transport,
                    'message': buffer,
                    'remaining': 1
                }
                if 'address' in config:
                    data['send_to'] = config['address']
                if 'callback' in config:
                    data['callback'] = config['callback']
                if 'id_object' in config:
                    data['id_object'] = config['id_object']
                if 'id_firm' in config:
                    data['id_firm'] = config['id_firm']
                if 'from' in config:
                    data['params'] = {}
                    data['params']['from'] = config['from']
                log.debug('Sending AMQP message to [work.process]...')
                broker.send([data],
                    routing_key = 'n.work.work.process',
                    exchangeName = 'n.work')

        if transport == "sms":
            # immediate sending of command update message
            broker.sendAmqpAnswer(self.uid,
                "Command was successfully received and processed")

    def initAmqpCommandThread(self):
        """
         AMQP thread initialization
        """
        if not self.uid:
            log.error('initAmqpCommandThread(): self.uid is empty!')
            return
        # start message broker thread for receiving tcp commands
        from lib.broker import MessageBrokerCommandThread
        log.debug('%s::initAmqpCommandThread()', self.__class__)
        MessageBrokerCommandThread(self)

    @classmethod
    def initAmqpThread(cls, protocol):
        """
         AMQP thread initialization
        """
        log.debug('%s::initAmqpThread() / %s', cls, protocol)
        # start message broker thread for receiving sms commands
        from lib.broker import MessageBrokerThread
        MessageBrokerThread(cls, protocol)
