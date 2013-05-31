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

# connections
username = 'guest'
password = 'guest'
host = '192.168.1.12'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:

    with conn.Consumer([Queue('maprox.mon.device.packet.create.worker6',
            exchange = device_exchange,
            routing_key='dhjsfkljhasdlfkhjasdhf')],
                       callbacks = [process_task]) as consumer:
        print('before')
        try:
            conn.drain_events(timeout=1)
        except:
            # no messages in queue
            pass
        print('after')