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
            #self.initQueues()
        except:
            pass

    def initExchanges(self):
        """
         Exchanges initialization
         @return:
        """
        self._exchanges = {
            'mon.device': Exchange(
                'mon.device', 'topic', durable = True)
        }

    def initQueues(self):
        """
         Queues initialization
         @return:
        """
        self._queues = {}
        for i in range(0, 16):
            workerNum = hex(i)[2:].upper()
            queueName = self.getRoutingKey(workerNum)
            self._queues[queueName] = Queue(
                queueName,
                exchange = self._exchanges['mon.device'],
                routing_key = queueName
            )

    def getRoutingKey(self, imei):
        """
         Returns routing key name by device imei
         @param imei: device ideintifier
        """
        #workerNum = '0'
        #if imei and len(imei) > 0:
        #    workerNum = imei[-1:].upper()
        #if workerNum not in '0123456789ABCDEF':
        #    workerNum = '0'
        #routingKey = 'maprox.mon.device.' + \
        #            'packet.create.worker%s' % workerNum
        routingKey = 'production.mon.device.packet.create.*'
        return routingKey

    def sendPackets(self, packets):
        """
         Sends packets to the message broker
         @param packets: list of dict
         @return:
        """
        exchange = self._exchanges['mon.device']
        with Connection(conf.amqpConnection) as conn:
            log.debug('BROKER: Connected to %s' % conf.amqpConnection)
            with conn.Producer(serializer = 'json') as producer:
                for packet in packets:
                    uid = None if 'uid' not in packet else packet['uid']
                    producer.publish(
                        packet,
                        exchange = exchange,
                        routing_key = self.getRoutingKey(uid)
                    )
                    if uid:
                        log.debug('Packet for "%s" is sent via message broker'
                            % uid)
                    else:
                        log.debug('Packet is sent via message broker')
        log.debug('BROKER: Disconnected')

broker = MessageBroker()