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
        'guid': 'SOME GUID',
        'uid': '359772039662797',
        'command': 'restart_tracker',
        'transport': 'tcp',
        'params': {
        }
    }
    with conn.Producer(serializer = 'json') as producer:
        rkey = 'production.mon.device.command.' + data['uid']
        packet_queue = Queue(
            rkey,
            exchange = device_exchange,
            routing_key = rkey
        )
        producer.publish(data,
            exchange = device_exchange,
            routing_key = rkey,
            declare=[packet_queue]
        )
        print(data)