# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
'''

from threading import Thread
from kernel.config import conf
from kernel.logger import log
from kombu import Connection, Exchange, Queue
import anyjson

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
        self.initExchanges()

    def initExchanges(self):
        """
         Exchanges initialization
         @return:
        """
        self._exchanges = {
            'mon.device': Exchange(
                'mon.device', 'topic', durable = True)
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
        routingKey = 'production.mon.device.' + \
            'packet.create.worker%s' % workerNum
        return routingKey

    def getConnection(self, imei):
        """
          Returns an AMQP connection handler
          @param imei: imei of the device
        """
        if not imei in self._connections:
            self._connections[imei] = Connection(conf.amqpConnection)
        return self._connections[imei]

    def getCommand(self, imei):
        """
          Returns an AMQP message from local buffer
          @param imei: imei of the device
        """
        if not imei in self._commands: return None
        return self._commands[imei]

    def send(self, packets, routing_key = None):
        """
         Sends packets to the message broker
         @param packets: list of dict
         @return:
        """
        exchange = self._exchanges['mon.device']
        with Connection(conf.amqpConnection) as conn:
            with conn.Producer(serializer = 'json') as producer:
                log.debug('BROKER: Connected to %s' % conf.amqpConnection)
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']

                    rkey = routing_key
                    if not routing_key:
                        rkey = self.getRoutingKey(uid)

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

    def sendAmqpAnswer(self, imei, data):
        """
          Response on amqp comand
        """
        command = self.getCommand(imei)
        if not command:
            log.debug("Error: no command found for %s!" % imei)
            return

        log.debug("Processing AMQP command answer")

        guid = command['body']['guid']

        data_string = data
        if not isinstance(data, str):
            data_string = data.get_parameters_string()

        answer_update = {
            "guid": guid,
            "status": COMMAND_STATUS_SUCCESS,
            "data": data_string
        }

        log.debug("Sending answer: %s" % answer_update)

        self.send([answer_update],
            routing_key = "production.mon.device.command.update")

        command['message'].ack()

        conn = self.getConnection(imei)
        conn.release()

        del self._connections[imei]
        del self._commands[imei]

    def sendAmqpError(self, imei, data, error):
        """
          Response on amqp comand
        """
        command = self.getCommand(imei)
        if not command:
            log.debug("Error: no command found for %s!" % imei)
            return

        guid = command['body']['guid']
        error_update = {
            "guid": guid,
            "status": COMMAND_STATUS_ERROR,
            "data": error
        }

        self.send([error_update],
            routing_key = "production.mon.device.command.update")

        command['message'].ack()

        conn = self.getConnection(imei)
        conn.release()

        del self._connections[imei]
        del self._commands[imei]

    def getCommands(self, imei):
        """
        Receives packets from the message broker.
        Runs until receives packet or timeout passes
        @return: received packets
        """
        device_exchange = Exchange(
            'maprox.mon.device',
            'topic',
            durable = True
        )

        conn = self.getConnection(imei)
        routing_key = 'production.mon.device.command.' + str(imei)
        command_queue = Queue(
            routing_key,
            exchange = device_exchange,
            routing_key = routing_key)

        with conn.Consumer([command_queue],
                callbacks = [self.onCommand]) as consumer:
            try:
                conn.drain_events(timeout=1)
            except:
                pass

        command = self.getCommand(imei)
        commandBody = None
        if command and ('body' in command):
            commandBody = command['body']
        return commandBody

    def onCommand(self, body, message):
        """
          Callback on AMQP message receiving
        """
        log.debug("Got AMQP message %s" % body)
        command = body
        if type(body) == str:
            command = anyjson.deserialize(body)
        self._commands[command["uid"]] = {
            "message": message,
            "body": body
        }

# --------------------------------------------------------------------

class MessageBrokerThread:
    """
     Message broker thread for receiving AMQP commands
    """

    _exchanges = None
    _protocolHandlerClass = None
    _protocolAlias = None
    _thread = None

    def __init__(self, protocolHandlerClass, protocolAlias):
        """
         Creates broker thread for listening AMQP commands sent to
         the specified protocol (usually for sms transport)
         @param handlerClass: protocol handler class
         @param protocolAlias: protocol alias
        """
        log.debug('%s::__init__()', self.__class__)
        self._protocolHandlerClass = protocolHandlerClass
        self._protocolAlias = protocolAlias
        self.initExchanges()
        # starting amqp thread
        self._thread = Thread(target = self.threadHandler)
        self._thread.start()

    def initExchanges(self):
        """
         Exchanges initialization
         @return:
        """
        self._exchanges = {
            'mon.device': Exchange(
                'mon.device', 'topic', durable = True)
        }

    def threadHandler(self):
        """
         Thread handler
        """
        while True:
            log.debug('%s: Init the AMQP connection...', self.__class__)
            commandRoutingKey = 'production.mon.device.command.' + \
                self._protocolAlias
            commandQueue = Queue(
                commandRoutingKey,
                exchange = self._exchanges['mon.device'],
                routing_key = commandRoutingKey
            )
            try:
                with Connection(conf.amqpConnection) as conn:
                    with conn.Consumer([commandQueue],
                        callbacks = [self.onCommand]) as consumer:
                        log.debug('%s: Successfully connected to %s',
                            self.__class__, conf.amqpConnection)
                        while True:
                            conn.drain_events()
            except Exception as E:
                log.error('%s: AMQP Error - %s', self.__class__, E)

    def onCommand(self, body, message):
        """
         Executes when command is received from queue
         @param body: amqp message body
         @param message: message instance
        """
        import kernel.pipe as pipe
        log.debug('%s: Received AMQP command = %s', self.__class__, body)

        command = body
        if type(body) == str:
            command = anyjson.deserialize(body)

        handler = self._protocolHandlerClass(pipe.Manager(), False)
        handler.processProtocolCommand(command)

        message.ack()

broker = MessageBroker()