import asyncio
import functools
import threading
import time
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


class AsyncRabbitPublisher:

    NEW = 0
    CONNECTED = 1
    CLOSED = 2

    def __init__(self, url, exchange, on_connected_callback=None, on_error_callback=None):
        self._on_connected_callback = on_connected_callback
        self._on_error_callback = on_error_callback

        self.lock = threading.Lock()
        self._loop = asyncio.get_event_loop()

        self._url = url
        self._exchange = exchange

        self._conn = None
        self._channel = None

        self._state = self.NEW

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

    def connect(self):
        AsyncioConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self._on_connection_open,
            on_open_error_callback=self._on_connection_error,
            on_close_callback=self._on_connection_close,
            custom_ioloop=self._loop)

        self._loop.run_forever()

    def publish(self, message):
        """Publishes message in a thread safe manner."""
        synchronise(self.lock, self._publish_sync, message)

    def close(self):
        """Closes the connection in a thread safe manner."""
        synchronise(self.lock, self._close_sync)

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

    def _on_message_returned(self, channel, frame, properties, body):
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
        self._loop.stop()

    # ERROR HANDLERS

    def _on_connection_error(self, _, e):
        if self._on_error_callback:
            self._on_error_callback(e)
        self._shutdown()

    def _on_connection_close(self, _, reason):
        self._loop.stop()
        if reason.reply_code != 200 and self._on_error_callback:
            self._on_error_callback(
                Exception(f'Unexpected connection shutdown, reason="{reason.reply_text}".'))
        self._shutdown()

    def _on_channel_close(self, _, reason):
        if reason.reply_code != 200 and self._on_error_callback:
            self._on_error_callback(
                Exception(f'Unexpected channel shutdown, reason="{reason.reply_text}".'))
            self._close()


class RabbitMqPublisher:

    def __init__(self, url, exchange):
        self._url = url
        self._exchange = exchange

        self._conn = None
        self._channel = None

    def connect(self):
        self._conn = pika.BlockingConnection(
            pika.URLParameters(self._url))

        self._channel = self._conn.channel()
        self._channel.exchange_declare(self._exchange, exchange_type='fanout')
        self._channel.confirm_delivery()

    def close(self):
        if self._conn and self._conn.is_open:
            self._conn.close()

    def publish(self, message):
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key='',
            body=message,
            mandatory=True)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # with RabbitMqPublisher('amqp://admin:admin@localhost:5672/articles', exchange='feed') as publisher:
    #     while True:
    #         publisher.publish('Hello world!')
    pub = AsyncRabbitPublisher('amqp://admin:admin@localhost:5672/articles', exchange='feed',
                               on_connected_callback=None, on_error_callback=lambda e: print(type(e)))
    pub.set_on_delivery_confirmation_callback(lambda tag, x: print(tag, x))
    pub.set_on_message_returned_callback(lambda reason, body: print(reason, body))
    threading.Thread(target=pub.connect).start()
    time.sleep(2)
    pub.publish('Hello world!')
    pub.close()
