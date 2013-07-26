import time
from kombu import Connection, Exchange, Queue

def publish(threadname):

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
            'params': {
                'threadname': threadname
            }
        }
        with conn.Producer(serializer = 'json') as producer:
            rkey = 'production.mon.device.command.globalsat_gtr128'
            command_queue = Queue(
                rkey,
                exchange = device_exchange,
                routing_key = rkey
            )
            for i in range(0, 20):
                data['guid'] += 1
                producer.publish(data,
                    exchange = device_exchange,
                    routing_key = rkey,
                    declare = [command_queue]
                )
                print(data)
                time.sleep(0.5)

import threading
for i in range(0, 3):
    threading.Thread(
        target = publish,
        name = "t" + str(i),
        args = ["t" + str(i)]
    ).start()
