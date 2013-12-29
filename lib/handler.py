# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Abstract class for all implemented protocols
@copyright 2009-2013, Maprox LLC
"""

from datetime import datetime
import os
import binascii
import base64
import socket
from kernel.utils import NeedMoreDataException
from kernel.logger import log
from kernel.config import conf
from lib.broker import broker


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
        self.__handlerId = binascii.hexlify(os.urandom(4)).decode()
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
        log.debug('[%s] initialization', self.handlerId)
        broker.handlerInitialize(self)

    def finalization(self):
        """
         Finalization of the handler.
         Free allocated resources.
         @return:
        """
        log.debug('[%s] finalization', self.handlerId)
        broker.handlerFinalize(self)

    @property
    def handlerId(self):
        return self.__handlerId

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
        log.debug('[%s] dispatch()', self.handlerId)
        buffer = self.recv()
        while len(buffer) > 0:
            self.processData(buffer)
            buffer = self.recv()
        log.debug('[%s] dispatch() - EXIT (empty buffer?)', self.handlerId)

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
                if self._buffer is None:
                    self._buffer = b''
                self._buffer += data
                protocolPackets = (
                    self._packetsFactory.getPacketsFromBuffer(self._buffer)
                )
                for protocolPacket in protocolPackets:
                    self.processProtocolPacket(protocolPacket)
                self._buffer = None
            except NeedMoreDataException as E:
                log.info('[%s] Need more data...', self.handlerId)
                return
            except Exception as E:
                log.error("[%s] processData error: %s", self.handlerId, E)

        log.debug('[%s] Checking handler commands', self.handlerId)
        if not self.needProcessCommands():
            return self
        log.debug('[%s] Ok we can process commands!', self.handlerId)

        self.processCommands()
        return self

    def processProtocolPacket(self, protocolPacket):
        """
         Process protocol packet.
         @type protocolPacket: packets.Packet
         @param protocolPacket: Protocol packet
        """
        pass

    def recv(self):
        """
         Receiving data from socket
         @return: String representation of data
        """

        sock = self.getThread().request
        sock.settimeout(60) # timeout eq. 5 seconds
        total_data = []
        while True:
            try:
                data = sock.recv(conf.socketPacketLength)
            except socket.timeout:
                self.processEvents()
                continue
            except Exception as E:
                log.debug('[%s] %s', self.handlerId, E)
                break
            log.debug('[%s] Data chunk = %s', self.handlerId, data)
            total_data.append(data)
            # I don't know why [if not data: break] is not working,
            # so let's do break here
            if len(data) < conf.socketPacketLength: break
        log.debug('[%s] Total data = %s', self.handlerId, total_data)

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
            log.error("[%s] Handler thread is not found!", self.handlerId)
        return self

    def processEvents(self):
        """
         Process some events while waiting for data from device
         @return:
        """
        pass

    def store(self, packets):
        """
         Sends a list of packets to store
         @param packets: A list of packets
         @return: Instance of lib.falcon.answer.FalconAnswer
        """
        result = self.getStore().send(packets)
        if result.isSuccess():
            log.debug('[%s] store() ... OK', self.handlerId)
        else:
            errorsList = result.getErrorsList()
            log.error('[%s] store():\n %s', self.handlerId, errorsList)
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
            log.error('[%s] Cant send an image - self.uid is not defined!',
                self.handlerId)
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
            log.info('[%s] sendImages(): Images have been sent.',
              self.handlerId)
        else:
            # ? Error messages should be converted into readable format
            log.error('[%s] sendImages():\n %s',
              self.handlerId, result.getErrorsList())

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

    def processCommands(self):
        """
         Processing AMQP commands for current device
        """
        try:
            if not self._commandsFactory:
                raise Exception("_commandsFactory is not defined!")
            commands = broker.getCommands(self)
            if commands:
                log.debug("[%s] Received commands are: %s",
                    self.handlerId, commands)
                self.processCommand(commands)
        except Exception as E:
            log.error('[%s] %s', self.handlerId, E)

    def processCommand(self, command):
        """
         Processing AMQP command
         @param command: command
        """
        if not command:
            log.error("[%s] Empty command description!", self.handlerId)
            return

        if (not self.uid) and ('uid' in command):
            self.uid = command['uid']

        log.debug("[%s] Processing AMQP command: %s ", self.handlerId, command)
        try:
            if not self._commandsFactory:
                raise Exception("_commandsFactory is not defined!")
            commandName = command["command"]
            commandInstance = self._commandsFactory.getInstance(command)
            if commandInstance:
                log.debug("[%s] Command class is %s",
                    self.handlerId, commandInstance.__class__)
                self.sendCommand(commandInstance, command)
            else:
                broker.sendAmqpError(self, "Command is not supported")
                log.error("[%s] No command with name %s",
                    self.handlerId, commandName)
        except Exception as E:
            log.error("[%s] Send command error is %s", self.handlerId, E)

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
                log.debug('[%s] Command data is sent: %s',
                    self.handlerId, buffer)
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
                log.debug('[%s] Sending AMQP message to [work.process]...',
                    self.handlerId)
                broker.send([data],
                    routing_key = 'n.work.work.process',
                    exchangeName = 'n.work')

        if transport == "sms":
            # immediate sending of command update message
            broker.sendAmqpAnswer(self,
                "Command was successfully received and processed")

    #def initAmqpCommandThread(self):
    #    """
    #     AMQP thread initialization
    #    """
    #    if not self.uid:
    #        log.error('initAmqpCommandThread(): self.uid is empty!')
    #        return
    #    # start message broker thread for receiving tcp commands
    #    from lib.broker import MessageBrokerCommandThread
    #    log.debug('%s::initAmqpCommandThread()', self.__class__)
    #    MessageBrokerCommandThread(self)

    @classmethod
    def initAmqpThread(cls, protocol):
        """
         AMQP thread initialization
        """
        log.debug('%s::initAmqpThread() / %s', cls, protocol)
        # start message broker thread for receiving sms commands
        from lib.broker import MessageBrokerThread
        MessageBrokerThread(cls, protocol)
