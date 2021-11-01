import asyncio
import threading
import time
from abc import ABC, abstractmethod

import pika
from pika.adapters.asyncio_connection import AsyncioConnection


def synchronise(lock, func, *args, **kwargs):
    lock.acquire(blocking=True)
    try:
        obj = func(*args, **kwargs)
    except Exception as e:
        raise e
    finally:
        lock.release()
    return obj


class AbstractAsyncPublisher(ABC):

    @abstractmethod
    def set_on_connected_callback(self, on_connected_callback):
        pass

    @abstractmethod
    def set_on_error_callback(self, on_error_callback):
        pass

    @abstractmethod
    def set_on_message_returned_callback(self, on_message_returned_callback):
        pass

    @abstractmethod
    def set_on_delivery_confirmation_callback(self, on_delivery_confirmation_callback):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def publish(self, message):
        pass

    @abstractmethod
    def close(self):
        pass


class AsyncRabbitPublisher(AbstractAsyncPublisher):

    NEW = 0
    CONNECTED = 1
    CLOSED = 2

    def __init__(self, url, exchange):
        self._lock = threading.Lock()
        self._loop = asyncio.get_event_loop()

        self._url = url
        self._exchange = exchange

        self._conn = None
        self._channel = None

        self._state = self.NEW

        self._on_connected_callback = None
        self._on_error_callback = None
        self._on_message_returned_callback = None
        self._delivery_confirmation_callback = None

    def set_on_connected_callback(self, on_connected_callback):
        self._on_connected_callback = on_connected_callback

    def set_on_error_callback(self, on_error_callback):
        self._on_error_callback = on_error_callback

    def set_on_message_returned_callback(self, on_message_returned_callback):
        self._on_message_returned_callback = on_message_returned_callback

    def set_on_delivery_confirmation_callback(self, on_delivery_confirmation_callback):
        self._delivery_confirmation_callback = on_delivery_confirmation_callback

    async def connect(self):
        AsyncioConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self._on_connection_open,
            on_open_error_callback=self._on_connection_error,
            on_close_callback=self._on_connection_close,
            custom_ioloop=self._loop)

    def publish(self, message):
        """Publishes message in a thread safe manner."""
        synchronise(self._lock, self._publish_sync, message)

    def close(self):
        """Closes the connection in a thread safe manner."""
        synchronise(self._lock, self._close_sync)

    # PROTECTED METHODS

    def _on_connection_open(self, connection: AsyncioConnection):
        self._conn = connection
        self._conn.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        self._channel = channel
        self._channel.add_on_close_callback(self._on_channel_close)
        self._channel.add_on_return_callback(self._on_message_returned)
        self._channel.confirm_delivery(self._on_delivery_confirmation)
        self._ensure_exchange_declared()

    def _ensure_exchange_declared(self):
        self._channel.exchange_declare(
            exchange=self._exchange,
            exchange_type='fanout',
            callback=self._on_exchange_declared)

    def _on_exchange_declared(self, frame):
        # Now we are sure that connection is open and everything works fine.
        self._state = self.CONNECTED
        print('CONNECTED')
        while True:
            pass

    # SYNCHRONISED METHODS

    def _close_sync(self):
        if self._state != self.CONNECTED:
            raise Exception('Cannot close not open connection.')
        self._loop.call_soon_threadsafe(self._close)

    def _publish_sync(self, message):
        if self._state != self.CONNECTED:
            raise Exception('Cannot publish on closed connection.')
        self._loop.call_soon_threadsafe(self._publish, message)

    # OTHER METHODS

    def _publish(self, message):
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key='',
            body=message,
            mandatory=True)

    def _on_message_returned(self, _, frame, __, body):
        if self._on_message_returned_callback:
            self._on_message_returned_callback(frame.reply_text, body)

    def _on_delivery_confirmation(self, frame):
        confirmation_type = frame.method.NAME.split('.')[1].lower()
        if self._delivery_confirmation_callback:
            self._delivery_confirmation_callback(
                frame.method.delivery_tag, confirmation_type)

    def _close(self):
        if self._conn is not None:
            self._conn.close()

    def _shutdown(self):
        self._state = self.CLOSED
        # self._loop.stop()

    # ERROR HANDLERS

    def _on_connection_error(self, _, e):
        if self._on_error_callback:
            self._on_error_callback(e)
        self._shutdown()

    def _on_connection_close(self, _, reason):
        if reason.reply_code != 200 and self._on_error_callback:
            self._on_error_callback(
                Exception(f'Unexpected connection shutdown, reason="{reason.reply_text}".'))
        self._shutdown()

    def _on_channel_close(self, _, reason):
        if reason.reply_code != 200 and self._on_error_callback:
            self._on_error_callback(
                Exception(f'Unexpected channel shutdown, reason="{reason.reply_text}".'))
            self._close()


class EventQueueException(Exception):
    pass


class MessageReturnedException(Exception):
    pass


class AbstractEventQueuePublisher(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def publish(self, message):
        pass

    @abstractmethod
    def close(self):
        pass


class RabbitMQPublisher(AbstractEventQueuePublisher):

    def __init__(self, url, exchange):
        self._url = url
        self._exchange = exchange
        self._channel: pika.adapters.blocking_connection.BlockingChannel = None
        self._conn: pika.adapters.BlockingConnection = None

    def connect(self):
        try:
            self._connect()
        except Exception as e:
            raise EventQueueException("Connection to event queue failed") from e

    def publish(self, message):
        try:
            self._publish(message)
        except pika.exceptions.UnroutableError as e:
            raise MessageReturnedException("Event queue returned a message") from e
        except Exception as e:
            raise EventQueueException("Failed to publish a message") from e

    def _connect(self):
        self._conn = pika.BlockingConnection(pika.URLParameters(url=self._url))
        channel = self._conn.channel()
        channel.exchange_declare(exchange=self._exchange, exchange_type='fanout')
        channel.confirm_delivery()
        self._channel = channel

    def _publish(self, message):
        self._channel.basic_publish(
            exchange='feed',
            routing_key='',
            body=message,
            mandatory=True)

    def close(self):
        if self._conn:
            self._conn.close()


if __name__ == '__main__':
    # asyncio.get_event_loop().run_until_complete(main())
    pub = Publisher('amqp://guest:guest@localhost:5672/%2f?heartbeat=5')

