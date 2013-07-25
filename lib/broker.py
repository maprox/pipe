# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
"""

from threading import Thread
from kernel.config import conf
from kernel.logger import log
from kombu import Connection, Exchange, Queue
import json

COMMAND_STATUS_CREATED = 1
COMMAND_STATUS_SUCCESS = 2
COMMAND_STATUS_ERROR = 3

class MessageBroker:
    """
     RabbitMQ message broker
    """

    _exchanges = None
    _connections = None
    _commands = None

    def __init__(self):
        """
         Constructor. Creates local storage to be used by protocol handlers
        """
        log.debug('%s::__init__()', self.__class__)
        self._connections = {}
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

    def getConnection(self, handler):
        """
         Returns an AMQP connection handler
         @param handler: AbstractHandler
        """
        if not handler.uid in self._connections:
            self._connections[handler.uid] = Connection(conf.amqpConnection)
        return self._connections[handler.uid]

    def releaseHandlerConnection(self, handler):
        """
         Releases resources for specified handler
         @param handler: AbstractHandler
        """
        try:
            if handler.uid in self._connections:
                conn = self._connections[handler.uid]
                conn.release()
        except:
            pass

        if handler.uid in self._connections:
            del self._connections[handler.uid]

        if handler.uid in self._commands:
            del self._commands[handler.uid]

    def storeCommand(self, command, message):
        """
         Stores command as current
         @param handler: AbstractHandler
         @param command: Command object as dict or string
         @param message: AMQP message instance
         @return dict Command dict object
        """
        if isinstance(command, str):
            command = json.loads(command)
        self._commands[command["uid"]] = {
            "message": message,
            "content": command
        }
        return command

    def getCommand(self, handler):
        """
         Returns an AMQP message from local buffer
         @param handler: AbstractHandler
        """
        if not handler.uid in self._commands: return None
        return self._commands[handler.uid]

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
        with Connection(conf.amqpConnection) as conn:
            with conn.Producer(serializer = 'json') as producer:
                log.debug('BROKER: Connected to %s' % conf.amqpConnection)
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']

                    rkey = routing_key
                    if not routing_key:
                        rkey = self.getRoutingKey(uid)

                    rkey = conf.environment + '.' + rkey
                    packet_queue = Queue(
                        rkey,
                        exchange = exchange,
                        routing_key = rkey
                    )

                    producer.publish(
                        packet,
                        exchange = exchange,
                        routing_key = rkey,
                        declare = [packet_queue]
                    )
                    if uid:
                        log.debug('Packet for "%s" is sent via message broker'
                            % uid)
                    else:
                        log.debug('Message is sent via message broker')
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
            log.debug("Error: no command found for %s!" % handler.uid)
            return

        log.debug("Processing AMQP command answer")
        guid = command['content']['guid']

        data_string = data
        if not isinstance(data, str):
            data_string = data.get_parameters_string()

        answer_update = {
            "guid": guid,
            "status": status,
            "data": data_string
        }

        log.debug("Sending answer: %s" % answer_update)
        self.send([answer_update], routing_key = "mon.device.command.update")

        command['message'].ack()

        self.releaseHandlerConnection(handler)

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
        conn = self.getConnection(handler)
        routing_key = conf.environment + '.mon.device.command.' +\
            str(handler.uid)
        command_queue = Queue(
            routing_key,
            exchange = self._exchanges['mon.device'],
            routing_key = routing_key)

        with conn.Consumer([command_queue], callbacks = [self.onCommand]):
            try:
                conn.drain_events(timeout=1)
            except:
                pass

        command = self.getCommand(handler)
        content = None
        if command and ('content' in command):
            content = command['content']
        else:
            # release connection if there is no commands received
            self.releaseHandlerConnection(handler)
        return content

    def onCommand(self, body, message):
        """
         Callback on AMQP message receiving
         @param body: dict Message body
         @param message: AMQP message object
        """
        log.debug("Got AMQP message %s" % body)
        self.storeCommand(body, message)

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
        self.releaseHandlerConnection(handler)

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
        log.debug('%s::__init__()', self.__class__)
        self._protocolHandlerClass = protocolHandlerClass
        self._protocolAlias = protocolAlias
        # starting amqp thread
        self._thread = Thread(target = self.threadHandler)
        self._thread.start()


    def threadHandler(self):
        """
         Thread handler
        """
        while True:
            log.debug('Init the AMQP connection...')
            commandRoutingKey = conf.environment + '.mon.device.command.' + \
                self._protocolAlias
            commandQueue = Queue(
                commandRoutingKey,
                exchange = broker._exchanges['mon.device'],
                routing_key = commandRoutingKey
            )
            try:
                with Connection(conf.amqpConnection) as conn:
                    log.debug('Support for heartbeat: %s',
                        str(conn.supports_heartbeats))
                    with conn.Consumer([commandQueue],
                            callbacks = [self.onCommand]):
                        log.debug('Successfully connected to %s',
                            conf.amqpConnection)
                        while True:
                            conn.drain_events()
            except Exception as E:
                log.error('AMQP Error - %s', E)
                import time
                time.sleep(60) # sleep for 60 seconds after exception

    def onCommand(self, body, message):
        """
         Executes when command is received from queue
         @param body: amqp message body
         @param message: message instance
        """
        import kernel.pipe as pipe
        log.debug('Received AMQP command = %s', body)

        command = broker.storeCommand(body, message)
        handler = self._protocolHandlerClass(pipe.Manager(), False)
        handler.processCommand(command)

# --------------------------------------------------------------------

class MessageBrokerCommandThread:
    """
     Message broker thread for receiving AMQP commands for particular device
    """

    _protocolHandler = None
    _thread = None

    def __init__(self, protocolHandler):
        """
         Creates broker thread for listening AMQP commands sent to
         the specific device (usually for sms transport)
         @param protocolHandlerClass: protocol handler class
         @param protocolAlias: protocol alias
        """
        log.debug('%s::__init__()', self.__class__)
        self._protocolHandler = protocolHandler
        # starting amqp thread
        self._thread = Thread(target = self.threadHandler)
        self._thread.start()


    def threadHandler(self):
        """
         Thread handler
        """
        while True:
            log.debug('Init the AMQP connection...')
            commandRoutingKey = conf.environment + '.mon.device.command.' +\
                                self._protocolAlias
            commandQueue = Queue(
                commandRoutingKey,
                exchange = broker._exchanges['mon.device'],
                routing_key = commandRoutingKey
            )
            try:
                with Connection(conf.amqpConnection) as conn:
                    with conn.Consumer([commandQueue],
                                       callbacks = [self.onCommand]):
                        log.debug('Successfully connected to %s',
                                  conf.amqpConnection)
                        while True:
                            conn.drain_events()
            except Exception as E:
                log.error('AMQP Error - %s', E)
                import time
                time.sleep(60) # sleep for 60 seconds after exception

    def onCommand(self, body, message):
        """
         Executes when command is received from queue
         @param body: amqp message body
         @param message: message instance
        """
        import kernel.pipe as pipe
        log.debug('Received AMQP command = %s', body)

        command = broker.storeCommand(body, message)
        handler = self._protocolHandlerClass(pipe.Manager(), False)
        handler.processCommand(command)

broker = MessageBroker()