from kombu import Connection, Exchange, Queue

device_exchange = Exchange('maprox.mon.device', 'topic', durable = True)

# connections
#username = 'maprox'
#password = 'gfhjkm'
username = 'guest'
password = 'guest'
host = '192.168.1.12'
url = 'amqp://{0}:{1}@{2}//'.format(username, password, host)

with Connection(url) as conn:

    # produce
    data = [{
        'imei': '2399230000000',
        'data': 'SOME DATA 1'
    }, {
        'imei': '2399230000001',
        'data': 'SOME DATA 2'
    }, {
        'imei': '2399230000000',
        'data': 'SOME DATA 3'
    }, {
        'imei': '2399230000002',
        'data': 'SOME DATA 4'
    }, {
        'imei': '239923003333a',
        'data': 'SOME DATA 5'
    }, {
        'imei': '2399230033323',
        'data': 'SOME DATA 6'
    }, {
        'imei': '2399230033330',
        'data': 'SOME DATA 7'
    }, {
        'imei': '2399230033332',
        'data': 'SOME DATA 8'
    }]
    with conn.Producer() as producer:
        for item in data:
            channel = item['imei'][-1:].upper()
            workerNum = 'packet.create.worker' + channel
            packet_queue = Queue(
                workerNum,
                exchange = device_exchange,
                routing_key = workerNum
            )
            producer.publish(None,
                headers = item,
                exchange = device_exchange,
                routing_key = workerNum,
                declare=[packet_queue]
            )
            print(item)