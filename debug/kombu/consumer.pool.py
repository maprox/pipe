import time
from kombu import BrokerConnection, Exchange, Queue
from kombu.pools import connections, producers
from copy import copy

command = []
def process_task(body, message):
    #command.append(22222)
    print(body)
    #message.ack()
    print(2)

device_exchange = Exchange('mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '127.0.0.1'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

connection = BrokerConnection(url)
with connections[connection].acquire(block=True) as conn:
    routing_key = 'production.mon.device.command.globalset_gtr128'

    command_queue = Queue(
        routing_key,
        exchange = device_exchange,
        routing_key = routing_key)

    with conn.Consumer([command_queue], callbacks = [process_task]):
        try:
            conn.ensure_connection()
            print(1)
            conn.drain_events(timeout = 1)
            print(3)
            print(command)
        except Exception as E:
            print(E)
    conn.release()

time.sleep(20)