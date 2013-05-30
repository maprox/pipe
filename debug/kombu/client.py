from kombu.utils import kwdict
from kombu import Connection, Exchange, Queue

def process_task(body, message):
    print(message.headers)
    print(body)
    message.ack()

device_exchange = Exchange(
    'maprox.mon.device',
    'topic',
    durable = True
)

import binascii

queues = []
for i in range(0, 16):
    workerNum = hex(i)[2:].upper()
    queues.append(Queue(
        'packet.create.worker%s' % workerNum,
        exchange = device_exchange,
        routing_key = 'packet.create.worker%s' % workerNum
    ))

# connections
#username = 'maprox'
#password = 'gfhjkm'
#host = 'localhost'
username = 'guest'
password = 'guest'
host = '192.168.1.12'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:

    with conn.Consumer(queues,
        callbacks = [process_task]
    ) as consumer:
        while True:
            conn.drain_events()