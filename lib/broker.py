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
        self._drainedBody = 0
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
        
        #    self._receive_exchange = Exchange('production.mon.device.command.create')

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
                    #routing_key = self.getRoutingKey(uid)
                    
                    routing_key = 'production.mon.device.packet.create'
                    
                    packet_queue = Queue(
                        routing_key,
                        exchange = exchange,
                        routing_key = routing_key
                    )
                    
                    producer.publish(
                        packet,
                        exchange = exchange,
                        routing_key = routing_key,
                        declare = [packet_queue]
                    )
                    if uid:
                        log.debug('Packet for "%s" is sent via message broker'
                            % uid)
                    else:
                        log.debug('Packet is sent via message broker')
        log.debug('BROKER: Disconnected')
    
    
    def receiveCallback(self, body, message):
        print(message.headers)
        print("Type of body is: %s" % type(body))
        print("Body is: %s" % body)
        self._drainedBody = body
        message.ack()
    
    def receivePackets(self):
        """
        Receives packets from the message broker.
        Runs until receives packet or timeout passes
        @return: received packets
        """
              
        self._drainedBody = 0
        
        device_exchange = Exchange(
            'maprox.mon.device',
            'topic',
            durable = True
        )
        
        #device_exchange = self._receive_exchange
        
        def process_task(body, message):
            print(message.headers)
            print("Type of body is: %s" % type(body))
            print("Body is: %s" % body)
            self.drainedBody = body
            message.ack()
        
        username = 'guest'
        password = 'guest'
        host = '10.233.10.13'
        url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

        with Connection(url) as conn:
            routing_key = 'production.mon.device.command.create'
            command_queue = Queue(routing_key, exchange = device_exchange, routing_key = routing_key)
            print(1111111)
            with conn.Consumer([command_queue], callbacks = [self.receiveCallback]) as consumer:
                print(222222)
                print('before')
                try:
                    conn.drain_events(timeout=1)    
                except:
                    print("No messages")
                    #no messages in queue
                    pass
                print("Consuming: %s" % consumer.consume())
                print('after')
        print("Drained: %s" % self._drainedBody)
        return(self._drainedBody)
        
broker = MessageBroker()