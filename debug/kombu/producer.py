import time
from kombu import Connection, Exchange, Queue

device_exchange = Exchange('mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '127.0.0.1'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:

    # produce
    data = {
        'guid': 0,
        'uid': '359772039662797',
        'command': 'restart_tracker',
        'transport': 'sms',
        'params': {}
    }
    with conn.Producer(serializer = 'json') as producer:
        while True:
            rkey = 'production.mon.device.command.globalset_gtr128'
            data['guid'] += 1
            command_queue = Queue(
                rkey,
                exchange = device_exchange,
                routing_key = rkey
            )
            producer.publish(data,
                exchange = device_exchange,
                routing_key = rkey,
                declare = [command_queue]
            )
            print(data)
            time.sleep(1)