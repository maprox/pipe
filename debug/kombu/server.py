from kombu import Connection, Exchange, Queue

device_exchange = Exchange('maprox.mon.device', 'topic', durable = True)

# connections
username = 'guest'
password = 'guest'
host = '192.168.1.12'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:

    # produce
    data = [{
        'imei': '2399230033323',
        'data': 'SOME DATA 6',
        'list': {
            'SAMPLE': 'Messsage'
        }
    }]
    with conn.Producer(serializer = 'json') as producer:
        for item in data:
            channel = item['imei'][-1:].upper()
            workerNum = 'maprox.mon.device.packet.create.worker' + channel
            packet_queue = Queue(
                workerNum,
                exchange = device_exchange,
                routing_key = workerNum
            )
            producer.publish(item,
                exchange = device_exchange,
                routing_key = workerNum,
                declare=[packet_queue]
            )
            print(item)