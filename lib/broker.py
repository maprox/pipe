# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
"""

from datetime import datetime
from threading import Thread
from kernel.config import conf
from kernel.logger import log

from kombu import BrokerConnection, Exchange, Queue

import re
import json
import time
#import hashlib

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
         @param imei: device identifier
        """
        return 'mon.device.packet.create.%s' % imei

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

        try:
            with BrokerConnection(conf.amqpConnection) as conn:
                log.debug('BROKER: Connect to %s' % conf.amqpConnection)
                conn.connect()
                connChannel = conn.channel()
                queuesConfig = {}

                # spike-nail START
                timePrev = None
                # spike-nail END

                reUid = re.compile('[\w-]+')
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']
                    # we should check uid for correctness
                    if uid is None or not reUid.match(uid):
                        log.error('Incorrect UID: %s' % uid)
                        continue

                    timeCurr = None
                    if 'time' in packet:
                        timeCurr = packet['time']

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

                    # spike-nail START
                    if timePrev and timeCurr:
                        fmtDate = "%Y-%m-%dT%H:%M:%S.%f"
                        t1 = datetime.strptime(timeCurr, fmtDate)
                        t2 = datetime.strptime(timePrev, fmtDate)
                        if t2 > t1:
                            tt = t1
                            t1 = t2
                            t2 = tt
                        if (t1 - t2).seconds < 10:
                            log.debug('Skip packet with time = ' + timeCurr)
                            continue # skip this packet if it's too close
                    # spike-nail END

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
                            msg += 'packet[\'time\'] = ' + timeCurr

                            # spike-nail START
                            timePrev = packet['time']
                            # spike-nail END

                        log.debug(msg)
                    else:
                        log.debug('Message is sent via message broker')
                conn.release()
        except Exception as E:
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
        try:
            with BrokerConnection(conf.amqpConnection) as conn:
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
            log.error('[%s] %s', handler.handlerId, E)
        return content

    def onCommand(self, body, message):
        """
         Callback on AMQP message receiving
         @param body: dict Message body
         @param message: AMQP message object
        """
        log.debug("Got AMQP message %s" % body)
        self.storeCommand(body)
        message.ack()

    def storeCommand(self, command):
        """
         Stores command as current
         @param command: Command object as dict or string
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
            try:
                with BrokerConnection(conf.amqpConnection) as conn:
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
                log.error('[%s] %s', self._protocolAlias, E)
                time.sleep(60) # sleep for 60 seconds after exception

    def onCommand(self, body, message):
        """
         Executes when command is received from queue
         @param body: amqp message body
         @param message: message instance
        """
        import kernel.pipe as pipe
        log.debug('[%s] Received command = %s', self._protocolAlias, body)

        command = broker.storeCommand(body)
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