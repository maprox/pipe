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
        #    #workerNum = imei[-1:].upper()
        #    workerNum = "_" + imei
        #if workerNum not in '0123456789ABCDEF':
        #    workerNum = '0'
        #workerNum = 'maprox.mon.device.command.'+'123456'
        #
        #routingKey = 'production.mon.device.' + \
        #            'packet.create.worker%s' % workerNum
        #routingKey = 'maprox.mon.device.command.029830498234099'
        routingKey = "production.mon.device.packet.create.*"
        return routingKey
    
    def sendCommandPacketsAsDicts(self, commandPackets):
        commandPacketsDicts = [commandPacket.__dict__ for commandPacket in commandPackets]
        for commandPacketDict in commandPacketsDicts:
            for commandPacketDictField in commandPacketDict:
                print(commandPacketDictField, commandPacketDict[commandPacketDictField])
                if type(commandPacketDict[commandPacketDictField]) == bytes:
                    commandPacketDict[commandPacketDictField] = str(commandPacketDict[commandPacketDictField])
        print(commandPacketsDicts)
        commandPacketsDicts = [{"uid":"1137", "data":"This is command packet"}]
        self.sendPackets(commandPacketsDicts, True)
    
    def sendPackets(self, packets, is_command_packet = False):
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
                    routingKey = self.getRoutingKey(uid)
                    if is_command_packet:
                        routingKey = routingKey + ".command"
                    print(packet, exchange, routingKey)
                    
                    packet_queue = Queue(
                        routingKey,
                        exchange = exchange,
                        routing_key = routingKey
                    )
                    #print("We will now publish:")
                    #print(packet)
                    producer.publish(
                        packet,
                        exchange = exchange,
                        routing_key = routingKey,
                        declare=[packet_queue]
                    )
                    if uid:
                        log.debug('Packet for "%s" is sent via message broker'
                            % uid)
                    else:
                        log.debug('Packet is sent via message broker')
        log.debug('BROKER: Disconnected')

broker = MessageBroker()
packet = [{"uid": "215_315"}]