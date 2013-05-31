# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
'''

from kernel.config import conf
from kernel.logger import log
from kombu import Connection, Exchange, Queue

class MessageBroker:
    """
     RabbitMQ message broker
    """
    def __init__(self):
        """
         Constructor. Creates local storage to be used by protocol handlers
        """
        log.debug('%s::__init__()', self.__class__)
        try:
            self.initExchanges()
            self.initQueues()
        except:
            pass

    def initExchanges(self):
        """
         Exchanges initialization
         @return:
        """
        self._exchanges = {
            'maprox.mon.device': Exchange(
                'maprox.mon.device', 'topic', durable = True)
        }

    def initQueues(self):
        """
         Queues initialization
         @return:
        """
        self._queues = {}
        for i in range(0, 16):
            workerNum = hex(i)[2:].upper()
            queueName = 'maprox.mon.device.' + \
                        'packet.create.worker%s' % workerNum
            self._queues[queueName] = Queue(
                queueName,
                exchange = self._exchanges['maprox.mon.device'],
                routing_key = queueName
            )

    def sendPackets(self, packets):
        """
         Sends packets to the message broker
         @param packets: list of dict
         @return:
        """
        exchange = self._exchanges['maprox.mon.device']
        with Connection(conf.amqpConnection) as conn:
            log.debug('BROKER: Connected to %s' % conf.amqpConnection)
            with conn.Producer(serializer = 'json') as producer:
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']
                    workerNum = '0'
                    if uid and len(uid) > 0:
                        workerNum = uid[-1:].upper()
                    if workerNum not in '0123456789ABCDEF':
                        workerNum = '0'
                    queueName = 'maprox.mon.device.' + \
                                'packet.create.worker%s' % workerNum
                    if queueName not in self._queues:
                        raise Exception('Invalid queueName: %s' % queueName)
                    producer.publish(
                        packet,
                        exchange = exchange,
                        routing_key = queueName,
                        declare = [self._queues[queueName]]
                    )
                    if uid:
                        log.debug('Packet for "%s" is sent via message broker'
                            % uid)
                    else:
                        log.debug('Packet is sent via message broker')
        log.debug('BROKER: Disconnected')

broker = MessageBroker()