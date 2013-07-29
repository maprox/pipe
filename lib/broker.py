# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
"""

from threading import Thread
from kernel.config import conf
from kernel.logger import log

from kombu import BrokerConnection, Exchange, Queue

import json
import time

COMMAND_STATUS_CREATED = 1
COMMAND_STATUS_SUCCESS = 2
COMMAND_STATUS_ERROR = 3

class MessageBroker:
    """
     RabbitMQ message broker
    """

    _exchanges = None
    _commands = None

    def __init__(self):
        """
         Constructor. Creates local storage to be used by protocol handlers
        """
        log.debug('%s::__init__()', self.__class__)
        self._commands = {}
        self._exchanges = {
            'mon.device': Exchange('mon.device', 'topic', durable = True),
            'n.work': Exchange('n.work', 'topic', durable = True)
        }

    def getRoutingKey(self, imei):
        """
         Returns routing key name by device imei
         @param imei: device ideintifier
        """
        workerNum = '0'
        if imei and len(imei) > 0:
            workerNum = imei[-1:].upper()
        if workerNum not in '0123456789':
            workerNum = '0'
        routingKey = 'mon.device.packet.create.worker%s' % workerNum
        return routingKey

    def send(self, packets, routing_key = None, exchangeName = None):
        """
         Sends packets to the message broker
         @param packets: list of dict
         @param routing_key: str
         @param exchangeName: str
        """
        exchange = self._exchanges['mon.device']
        if (exchangeName is not None) and (exchangeName in self._exchanges):
            exchange = self._exchanges[exchangeName]

        with BrokerConnection(conf.amqpConnection) as conn:
            try:
                log.debug('BROKER: Connect to %s' % conf.amqpConnection)
                conn.connect()
                connChannel = conn.channel()
                queuesConfig = {}
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']

                    if not uid in queuesConfig:
                        routingKey = routing_key
                        if not routing_key:
                            routingKey = self.getRoutingKey(uid)

                        routingKey = conf.environment + '.' + routingKey
                        queuesConfig[uid] = {
                            'routingKey': routingKey,
                            'queue': Queue(
                                routingKey,
                                exchange = exchange,
                                routing_key = routingKey
                            )
                        }

                    config = queuesConfig[uid]
                    with conn.Producer(channel = connChannel) as producer:
                        conn.ensure_connection()
                        producer.publish(
                            packet,
                            exchange = exchange,
                            routing_key = config['routingKey'],
                            declare = [config['queue']],
                            retry = True
                        )
                    if uid:
                        msg = 'Packet for "%s" is sent. ' % uid
                        if 'time' in packet:
                            msg += 'packet[\'time\'] = ' + packet['time']
                        log.debug(msg)
                    else:
                        log.debug('Message is sent via message broker')
                conn.release()
            except Exception as E:
                if conn and conn.connected:
                    conn.release()
                log.error('Error during packet send: %s', E)
            log.debug('BROKER: Disconnected')

    def amqpCommandUpdate(self, handler, status, data):
        """
         Command update via message broker
         @param handler: AbstractHandler instance
         @param status: int Command status
         @param data: str Command data string
        """
        command = self.getCommand(handler)
        if not command:
            log.debug("[%s] Error: no command found for %s!",
                handler.handlerId, handler.uid)
            return

        log.debug("[%s] Processing AMQP command answer", handler.handlerId)
        guid = command['guid']

        data_string = data
        if not isinstance(data, str):
            data_string = data.get_parameters_string()

        answer_update = {
            "guid": guid,
            "status": status,
            "data": data_string
        }

        log.debug("[%s] Sending answer: %s", handler.handlerId, answer_update)
        self.send([answer_update], routing_key = "mon.device.command.update")
        self.clearCommand(command)

    def sendAmqpAnswer(self, handler, data):
        """
         Response on amqp comand
         @param handler: AbstractHandler instance
         @param data: str Command data
        """
        self.amqpCommandUpdate(handler, COMMAND_STATUS_SUCCESS, data)

    def sendAmqpError(self, handler, error):
        """
         Response on amqp comand
         @param handler: AbstractHandler instance
         @param error: str Command error string
        """
        self.amqpCommandUpdate(handler, COMMAND_STATUS_ERROR, error)

    def getCommands(self, handler):
        """
         Receives packets from the message broker.
         Runs until receives packet or timeout passes
         @param handler: AbstractHandler
         @return: received packets
        """
        content = None
        with BrokerConnection(conf.amqpConnection) as conn:
            try:
                routing_key = conf.environment + '.mon.device.command.' + \
                    str(handler.uid)
                log.debug('[%s] Check commands queue %s',
                    handler.handlerId, routing_key)
                command_queue = Queue(
                    routing_key,
                    exchange = self._exchanges['mon.device'],
                    routing_key = routing_key)

                conn.connect()
                with conn.Consumer([command_queue],
                    callbacks = [self.onCommand]):
                    conn.ensure_connection()
                    conn.drain_events(timeout = 1)
                    command = self.getCommand(handler)
                    if command:
                        log.debug('[%s] We got command: %s',
                            handler.handlerId, command)
                        content = command
                    else:
                        log.debug('[%s] No commands found', handler.handlerId)
                conn.release()
            except Exception as E:
                if conn and conn.connected:
                    conn.release()
                log.debug('[%s] %s', handler.handlerId, E)
        return content

    def onCommand(self, body, message):
        """
         Callback on AMQP message receiving
         @param body: dict Message body
         @param message: AMQP message object
        """
        log.debug("Got AMQP message %s" % body)
        self.storeCommand(body, message)
        message.ack()

    def storeCommand(self, command, message):
        """
         Stores command as current
         @param command: Command object as dict or string
         @param message: AMQP message instance
         @return dict Command dict object
        """
        if isinstance(command, str):
            command = json.loads(command)
        uid = command["uid"]
        if uid not in self._commands:
            self._commands[uid] = {}
        self._commands[uid][command['guid']] = command
        return command

    def getCommand(self, handler):
        """
         Returns an AMQP message from local buffer
         @param handler: AbstractHandler
        """
        if (handler.uid in self._commands) and self._commands[handler.uid]:
            for guid in self._commands[handler.uid]:
                return self._commands[handler.uid][guid]
        return None

    def clearCommand(self, command):
        """
         Removes command from local storage
         @param command: Command dict
        """
        uid = command['uid']
        guid = command['guid']
        if (uid in self._commands) and (guid in self._commands[uid]):
            del self._commands[uid][guid]

    def handlerInitialize(self, handler):
        """
         Initialization of handler
         @param handler: AbstractHandler
         @return:
        """

    def handlerUpdate(self, handler):
        """
         Update of handler
         @param handler: AbstractHandler
         @return:
        """

    def handlerFinalize(self, handler):
        """
         Finalization of handler
         @param handler: AbstractHandler
         @return:
        """

# --------------------------------------------------------------------

class MessageBrokerThread:
    """
     Message broker thread for receiving AMQP commands for a protocol
    """

    _protocolHandlerClass = None
    _protocolAlias = None
    _thread = None

    def __init__(self, protocolHandlerClass, protocolAlias):
        """
         Creates broker thread for listening AMQP commands sent to
         the specified protocol (usually for sms transport)
         @param protocolHandlerClass: protocol handler class
         @param protocolAlias: protocol alias
        """
        log.debug('%s::__init__(%s)', self.__class__, protocolAlias)
        self._protocolHandlerClass = protocolHandlerClass
        self._protocolAlias = protocolAlias
        # starting amqp thread
        self._thread = Thread(target = self.threadHandler)
        self._thread.start()

    def threadHandler(self):
        """
         Thread handler
        """
        commandRoutingKey = conf.environment + '.mon.device.command.' + \
            self._protocolAlias
        commandQueue = Queue(
            commandRoutingKey,
            exchange = broker._exchanges['mon.device'],
            routing_key = commandRoutingKey
        )
        while True:
            with BrokerConnection(conf.amqpConnection) as conn:
                try:
                    conn.connect()
                    conn.ensure_connection()
                    log.debug('[%s] Connected to %s',
                        self._protocolAlias, conf.amqpConnection)
                    with conn.Consumer([commandQueue],
                            callbacks = [self.onCommand]):
                        while True:
                            conn.ensure_connection()
                            conn.drain_events()
                    conn.release()
                except Exception as E:
                    if conn and conn.connected:
                        conn.release()
                    log.debug('[%s] %s', self._protocolAlias, E)
                    time.sleep(60) # sleep for 60 seconds after exception

    def onCommand(self, body, message):
        """
         Executes when command is received from queue
         @param body: amqp message body
         @param message: message instance
        """
        import kernel.pipe as pipe
        log.debug('[%s] Received command = %s', self._protocolAlias, body)

        command = broker.storeCommand(body, message)
        handler = self._protocolHandlerClass(pipe.Manager(), False)
        handler.processCommand(command)
        message.ack()

# --------------------------------------------------------------------

class MessageBrokerCommandThread:
    """
     Message broker thread for receiving AMQP commands for particular device
    """
    pass

broker = MessageBroker()