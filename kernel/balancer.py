# -*- coding: utf8 -*-
"""
@project   Maprox <http://www.maprox.net>
@info      Packet receive load balancer
@copyright 2013, Maprox LLC
"""

import time
import socket
import hashlib

from collections import deque

from threading import Thread
from kernel.logger import log
from kernel.config import conf
from lib.broker import broker
from kombu import BrokerConnection, Queue

# --------------------------------------------------------------------

QUEUE_PREFIX = conf.environment + '.mon.device.packet'
QUEUE_IN_PROGRESS_MESSAGE = 'Waiting...'

# --------------------------------------------------------------------

class PacketReceiveBalancer:
    """
     Packet receive load balancer
    """
    _threadSignalRequest = None
    _threadSignalResponse = None

    def __init__(self):
        """
         Balancer initialization
         @return: PacketReceiveBalancer instance
        """
        log.debug('%s::__init__()', self.__class__)

    def run(self):
        """
         Starts balancer
         @return:
        """
        self._receiveManager = PacketReceiveManager()
        self.initControlThreads()

    def initControlThreads(self):
        """
         Initialize control threads
         @return:
        """
        log.debug('%s::initControlThreads()', self.__class__)
        # starting request signal thread
        self._threadSignalRequest = Thread(
            target = self.threadSignalRequestHandler)
        self._threadSignalRequest.start()
        # starting response signal thread
        self._threadSignalResponse = Thread(
            target = self.threadSignalResponseHandler)
        self._threadSignalResponse.start()

    def threadSignalRequestHandler(self):
        threadName = 'SignalRequestThread'
        signalQueueName = QUEUE_PREFIX + '.signal.request'
        signalRoutingKey = QUEUE_PREFIX + '.create.#'
        signalQueue = Queue(
            signalQueueName,
            exchange = broker._exchanges['mon.device'],
            routing_key = signalRoutingKey
        )
        log.debug('%s::started', threadName)
        while True:
            try:
                with BrokerConnection(conf.amqpConnection) as conn:
                    conn.connect()
                    conn.ensure_connection()
                    log.debug('%s::Connected to %s',
                        threadName, conf.amqpConnection)
                    with conn.Consumer([signalQueue],
                           callbacks = [self.threadSignalRequestOnMessage]):
                        while True:
                            conn.ensure_connection()
                            conn.drain_events()
                    conn.release()
            except Exception as E:
                log.error('%s::%s', threadName, E)
                time.sleep(10) # sleep for 10 seconds after exception

    def threadSignalRequestOnMessage(self, body, message):
        """
         Executes when there is a packet in signal queue
         @param body: amqp message body
         @param message: message instance
        """
        threadName = 'SignalRequestThread'
        uid = 'unknown uid [!]'
        if 'uid' in body:
            uid = body['uid']
        log.debug('%s:: > Signal for %s', threadName, uid)
        self._receiveManager.checkListeningForQueue(uid)
        message.ack()

    def threadSignalResponseHandler(self):
        threadName = 'SignalResponseThread'
        signalRoutingKey = QUEUE_PREFIX + '.signal.response'
        signalQueue = Queue(
            signalRoutingKey,
            exchange = broker._exchanges['mon.device'],
            routing_key = signalRoutingKey
        )
        log.debug('%s::started', threadName)
        while True:
            try:
                with BrokerConnection(conf.amqpConnection) as conn:
                    conn.connect()
                    conn.ensure_connection()
                    log.debug('%s::Connected to %s',
                        threadName, conf.amqpConnection)
                    with conn.Consumer([signalQueue],
                        callbacks = [self.threadSignalResponseOnMessage]):
                        while True:
                            conn.ensure_connection()
                            conn.drain_events()
                    conn.release()
            except Exception as E:
                log.error('%s::%s', threadName, E)
                time.sleep(10) # sleep for 10 seconds after exception

    def threadSignalResponseOnMessage(self, body, message):
        """
         Executes when there is an answer in signal queue
         @param body: amqp message body
         @param message: message instance
        """
        threadName = 'SignalResponseThread'
        uid = 'unknown uid [!]'
        if 'uid' in body:
            uid = body['uid']
        log.debug('%s:: < Signal for %s', threadName, uid)
        self._receiveManager.checkListeningForQueue(uid)
        self._receiveManager.messageReceived(uid)
        message.ack()


# --------------------------------------------------------------------

class PacketReceiveManager:
    """
     Factory for packet receivers classes
    """
    _queues = None
    _messages = None
    _queuesListNew = None

    def __init__(self):
        """
         Class initialization
        """
        self._queues = {}
        self._messages = {}
        self._queuesListNew = []
        self.initReceiverThread()

    def initReceiverThread(self):
        """
         Initialize receiver thread
         @return:
        """
        log.debug('%s::initReceiverThread()', self.__class__)
        # starting request signal thread
        self._threadReceive = Thread(target = self.threadReceiveHandler)
        self._threadReceive.start()

    def threadReceiveHandler(self):
        threadName = 'ReceiverThread'
        log.debug('%s::started', threadName)
        while True:
            queues = []
            for key in self._queues:
                queues.append(self._queues[key])
            if not queues:
                time.sleep(2) # sleep for 2 seconds
                continue
            try:
                with BrokerConnection(conf.amqpConnection) as conn:
                    conn.connect()
                    conn.ensure_connection()
                    log.debug('%s::Connected to %s',
                        threadName, conf.amqpConnection)
                    with conn.Consumer(queues, callbacks = [
                        self.threadReceiverOnMessage
                    ]) as consumer:
                        while True:
                            conn.ensure_connection()
                            try:
                                conn.drain_events(timeout = 5) # 5 seconds
                            except socket.timeout:
                                pass
                            self.appendNewQueues(consumer)
                    conn.release()
            except Exception as E:
                log.error('%s::%s', threadName, E)
                time.sleep(30) # sleep for 30 seconds after exception

    def appendNewQueues(self, consumer):
        """
         Check for new queues in the list
         @param consumer: Consumer instance
        """
        if self._queuesListNew:
            for queue in self._queuesListNew:
                consumer.add_queue(queue)
            consumer.consume()
        self._queuesListNew = []

    def threadReceiverOnMessage(self, body, message):
        """
         Executes when there is a packet in signal queue
         @param body: amqp message body
         @param message: message instance
        """
        threadName = 'ReceiverThread'
        uid = 'unknown uid [!]'
        if 'uid' in body:
            uid = body['uid']
        if uid not in self._messages:
            self._messages[uid] = deque()
        # immediate send message if message queue is empty
        if not self._messages[uid]:
            self.sendMessage(uid, body)
        # store message to the queue
        self._messages[uid].append({
            "message": message,
            "body": body
        })
        log.debug('%s::Packet for %s added to the queue: %s',
            threadName, body['time'], uid)

    def checkListeningForQueue(self, uid):
        """
         Checks if manager is already listening the queue for specified uid.
         If not, it begins to consume from appropriate queue.
         @param uid: Device identifier
         @return:
        """
        if uid in self._queues: return
        routingKey = QUEUE_PREFIX + '.create.' + uid
        log.debug('--- ADDING QUEUE ---: %s', routingKey)
        self._queues[uid] = Queue(
            routingKey,
            exchange = broker._exchanges['mon.device'],
            routing_key = routingKey
        )
        self._queuesListNew.append(self._queues[uid])

    def getCheckFileName(self, uid):
        """
         Returns check file name by identifier uid
         @return: string
        """
        return './db/flb_' + hashlib.md5(uid.encode()).hexdigest()

    def sendMessage(self, uid, body = None, ignoreFlag = False):
        """
         Send message to the broker
         @param uid: Device identifier
         @param body: New packet body
        """
        try:
            checkFile = self.getCheckFileName(uid)
            with open(checkFile, 'a+') as f:
                if not body:
                    f.truncate(0)
                else:
                    f.seek(0)
                    flag = f.read()
                    if ignoreFlag or (flag != QUEUE_IN_PROGRESS_MESSAGE):
                        broker.send([body], 'mon.device.packet.receive')
                        f.truncate(0)
                        f.write(QUEUE_IN_PROGRESS_MESSAGE)
        except IOError as E:
            log.debug(E)

    def messageReceived(self, uid):
        """
         Mark first message from queue as received and send next
         @param uid: Device identifier
        """
        if uid not in self._messages:
            self._messages[uid] = deque()
        first = None
        if self._messages[uid]:
           first = self._messages[uid].popleft()
        nextBody = None
        if self._messages[uid]:
            next = self._messages[uid][0]
            nextBody = next['body']
        self.sendMessage(uid, nextBody, True)
        if first:
            first['message'].ack()

# --------------------------------------------------------------------

class PacketReceiver:
    """
     Packet receiver class for particular devices
    """
    _manager = None
    _queue = None

    def __init__(self, manager, uid):
        """
         Receiver initialization
         @param manager:
         @param uid:
        """
        log.debug('%s::__init__(%s)', self.__class__, uid)
        self._manager = manager
        self._uid = uid
        self._queue = QUEUE_PREFIX + '.create.' + uid
        log.debug('Queue: %s', self._queue)

    def refresh(self):
        """
         Refresh connection
        """
        log.debug('%s[%s]::Refresh', 'PacketReceiver', self._uid)