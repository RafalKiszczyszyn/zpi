import sys
import pika


def main():
    if len(sys.argv) != 3:
        print('Run rabbitmq_producer.py queue message')
        exit(1)
    queue = sys.argv[1]
    message = sys.argv[2]

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=message.encode(encoding='utf-8'))
    print(f" [x] Sent Message='{message}' to Queue='{queue}'")


if __name__ == '__main__':
    #sys.argv.append(
    #    '{"articles": [{"guid": "ABC1", "title": "Title 1", "summary": "Summary 1"}, ' +
    #    '{"guid": "ABC2", "title": "Title 2", "summary": "Summary 2"}]}'
    #)
    main()
