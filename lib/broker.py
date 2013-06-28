# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Working with RabbitMQ
@copyright 2013, Maprox LLC
'''

from kernel.config import conf
from kernel.logger import log
from kombu import Connection, Exchange, Queue
import anyjson

class MessageBroker:
    """
     RabbitMQ message broker
    """

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

    def sendPackets(self, packets,
            routing_key = 'production.mon.device.packet.create.*'):
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
        data_dict = data.get_dict()
        data_string = data.get_parameters_string()
        answer_update = {
            "guid": guid,
            "status": "2",
            "data": data_string
        }

        log.debug("Sending answer: %s" % answer_update)

        self.sendPackets([answer_update], 
            routing_key = "production.mon.device.command.update")

        command['message'].ack()

        conn = self.getConnection(imei)
        conn.release()

        delete self._connections[imei]
        delete self._commands[imei]

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
            "status": "3",
            "data": error
        }

        self.sendPackets([error_update], 
            routing_key = "production.mon.device.command.update")

        command['message'].ack()

        conn = self.getConnection(imei)
        conn.release()

        delete self._connections[imei]
        delete self._commands[imei]

    def receiveCallback(self, body, message):
        """
          Callback on AMQP message receiving
        """
        log.debug("Got AMQP message %s" % body)
        command = None
        if type(body) == dict:
            command = body
        elif type(body) == str:
            command = anyjson.deserialize(body)
        else:
            return
        self._commands[command["uid"]] = {
            "message": message,
            "body": body
        }

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
                callbacks = [self.receiveCallback]) as consumer:
            try:
                conn.drain_events(timeout=1)
            except:
                pass

        command = self.getCommand(imei)
        commandBody = None
        if command and ('body' in command):
            commandBody = command['body']
        return commandBody

broker = MessageBroker()