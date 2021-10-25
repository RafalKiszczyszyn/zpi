import pika


def main():
    credentials = pika.PlainCredentials('admin', 'admin')
    parameters = pika.ConnectionParameters('localhost', virtual_host='articles', credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()


if __name__ == '__main__':
    main()
