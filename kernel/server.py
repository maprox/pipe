# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      TCP-server
@copyright 2009-2012, Maprox LLC
'''

import traceback
from threading import Thread
from socketserver import TCPServer
from socketserver import ThreadingMixIn
from socketserver import BaseRequestHandler

from kernel.logger import log
from kernel.config import conf
from kernel.dispatcher import disp

# ===========================================================================
class ClientThread(BaseRequestHandler):
    """
     RequestHandler's descendant class for our server.
     An object of this class is created for each connection to the server.
     We override the "handle" method and communicate with the client in it.
    """

    def setup(self):
        pass

    def handle(self):
        try:
            disp.dispatch(self)
        except Exception as E:
            log.error("Dispatch error: %s", traceback.format_exc())

    def finish(self):
        pass

# ===========================================================================
class ThreadingServer(ThreadingMixIn, TCPServer):
    """
     Base class for tcp-server multithreading
    """
    allow_reuse_address = True

"""
def amqp_get_commands():
    from lib.handlers.list import handlersList
    from kombu import Connection, Exchange, Queue

    for h in handlersList:
        print(h)

    def process_task(body, message):
        #print(message.headers)
        print("Type of body is: %s" % type(body))
        print("Body is: %s" % body)
        for Handler in handlersList:
            #print(h.super().__dict__)
            try:
                Handler.processAmqpCommands(body)
            except E:
                print(E)
        message.ack()

    device_exchange = Exchange('production.mon.device.command.create', 
        'topic', durable = True)

    # connections
    username = 'guest'
    password = 'guest'
    host = '10.233.10.13'
    url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

    with Connection(url) as conn:
        routing_key = 'production.mon.device.command.create'
        command_queue = Queue(routing_key, exchange = device_exchange, 
            routing_key = routing_key)
        with conn.Consumer([command_queue], 
            callbacks = [process_task]) as consumer:
            print('before')
            while True:
                try:
                    conn.drain_events(timeout=1)
                    print(disp)
                except KeyboardInterrupt:
                    break
                except:
                    #print("No messages")
                    # no messages in queue
                    pass
            print('after')
"""
# ===========================================================================
class Server():
    """
     Multithreaded TCP-server
    """

    # -----------------------------
    def __init__(self, port = 30003):
        """
         Server class constructor
         @param port: Listening port. Optional, default is 30003.
        """
        log.debug("Server::__init__(%s)", port)
        self.host = ""
        self.port = port
        self.server = ThreadingServer((self.host, self.port), ClientThread)

    # -----------------------------
    def run(self):
        """
         Method wich starts TCP-server
        """
        log.debug("Server::run()")
        self.server_thread = Thread(target = self.server.serve_forever)
        #self.server_thread.daemon = True
        self.server_thread.setDaemon(conf.setDaemon)
        self.server_thread.start()
        log.info("Server is started on port %s", self.port)

    # -----------------------------
    def verify_request(self, request, client_address):
        """
         Check request in IP-list
        """
        log.debug("verify_request()")
        return True
