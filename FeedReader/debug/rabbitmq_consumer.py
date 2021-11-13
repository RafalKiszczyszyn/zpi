import pika


def on_message(channel, method_frame, header_frame, body):
    print('***MESSAGE***')
    print(method_frame.delivery_tag)
    print(body)
    print('***END OF MESSAGE***\n')
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def consume(url, exchange):
    conn = pika.BlockingConnection(pika.URLParameters(url))
    channel = conn.channel()
    frame = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
    channel.queue_bind(frame.method.queue, exchange)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=frame.method.queue, on_message_callback=on_message)
    channel.start_consuming()


def main():
    consume(url='amqp://guest:guest@localhost:5672/%2f?heartbeat=60', exchange='feed')


if __name__ == '__main__':
    main()
