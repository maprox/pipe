import time
from kombu import Connection, Exchange, Queue

def process_task(body, message):
    print(body)
    #message.ack()

device_exchange = Exchange('mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '10.233.2.31'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:
    #rkey = 'production.mon.device.command.0,\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    #rkey = 'production.mon.device.packet.create.0,\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    #rkey = 'production.mon.packet.create.0,\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    #rkey = 'production.mon.device.packet.create.8682040046074\x00\x0A'
    rkey = 'production.mon.device.command.8682040046074\x00\x0a'
    command_queue = Queue(
        rkey,
        exchange = device_exchange,
        routing_key = rkey
    )
    bound_queue = command_queue(conn.channel())
    bound_queue.delete()
    exit()

    with conn.Consumer(
        [command_queue],
        callbacks = [process_task]
    ) as consumer:
        try:
            while True:
                conn.drain_events()
        except:
            # no messages in queue
            pass