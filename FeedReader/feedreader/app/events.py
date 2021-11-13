import urllib.parse
from abc import ABC, abstractmethod
import pika


class EventQueueException(Exception):
    pass


class ConnectionException(Exception):
    pass


class IEventQueuePublisher(ABC):
    @abstractmethod
    def is_alive(self) -> bool:
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def keep_alive(self):
        pass

    @abstractmethod
    def publish(self, channel, message):
        pass

    @abstractmethod
    def close(self):
        pass


class RabbitMQPublisher(IEventQueuePublisher):

    def __init__(self, url, ssl_context=None):
        self._url = url
        self._channel: pika.adapters.blocking_connection.BlockingChannel = None
        self._conn: pika.adapters.BlockingConnection = None

        if ssl_context:
            self._enable_ssl(ssl_context)

    def is_alive(self) -> bool:
        if self._conn:
            return self._conn.is_open
        else:
            return False

    def connect(self):
        try:
            self._connect()
        except Exception as e:
            raise ConnectionException("Connection to an event queue failed") from e

    def keep_alive(self):
        self._conn.process_data_events()

    def publish(self, channel, message):
        try:
            self._channel.exchange_declare(exchange=channel, exchange_type='fanout')
            self._publish(exchange=channel, message=message)
        except Exception as e:
            raise EventQueueException("Failed to publish a message") from e

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _enable_ssl(self, ssl_context):
        ssl_options = urllib.parse.urlencode({'ssl_options': ssl_context})
        self._url += '&' + ssl_options \
            if self._url.find('?') != -1 \
            else '?' + ssl_options

    def _connect(self):
        self._conn = pika.BlockingConnection(pika.URLParameters(url=self._url))
        channel = self._conn.channel()
        channel.confirm_delivery()
        self._channel = channel

    def _publish(self, exchange, message):
        self._channel.basic_publish(
            exchange=exchange,
            routing_key='',
            body=message,
            mandatory=True)
