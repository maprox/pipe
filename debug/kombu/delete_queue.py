import time
from kombu import Connection, Exchange, Queue

device_exchange = Exchange('mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '127.0.0.1'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

print(url)

with Connection(url) as conn:
    keys = [
        'production.mon.device.command.86820ē8364\x0D\x0A\x0D\x0A',
        'production.mon.device.packet.create.86820ē8364\x0D\x0A\x0D\x0A'
    ]
    for rkey in keys:
        command_queue = Queue(
            rkey,
            exchange = device_exchange,
            routing_key = rkey
        )
        bound_queue = command_queue(conn.channel())
        bound_queue.delete()