import time
from kombu import Connection, Exchange, Queue

def process_task(body, message):
    print(body)
    message.ack()

device_exchange = Exchange('mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '127.0.0.1'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:
    rkey = 'production.mon.device.command.globalset_gtr128'
    command_queue = Queue(
        rkey,
        exchange = device_exchange,
        routing_key = rkey
    )
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