import asyncio
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple, Callable

import pika
from concurrent.futures import ThreadPoolExecutor


class Response(ABC):
    pass


@dataclass(frozen=True)
class Ack(Response):
    message: str


@dataclass(frozen=True)
class Nack(ABC):
    requeue: bool


class RabbitMqConsumer:

    # noinspection PyTypeChecker
    def __init__(self, loop: asyncio.AbstractEventLoop,
                 bindings: List[Tuple[str, Callable[[str], Response]]],
                 threads=1,
                 messages_limit=1):
        self._is_running = True
        self._loop = loop

        self._bindings = bindings

        self._connection: pika.adapters.blocking_connection.BlockingConnection = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel = None

        self._pool = ThreadPoolExecutor(threads)
        self._messages = set()
        self._msg_limit = messages_limit

    def consume(self):
        self._is_running = True
        self._connection = connection = pika.BlockingConnection()
        self._channel = connection.channel()
        self._channel.queue_declare('test', durable=False, auto_delete=True)
        self._loop.run_until_complete(self._consume())

    def stop(self):
        self._is_running = False

    async def _consume(self):
        while self._is_running:
            if len(self._messages) < self._msg_limit:
                for queue, on_message in self._bindings:
                    self._consume_once(queue, on_message)
            await asyncio.sleep(0.1)
        self._connection.close()
        self._loop.stop()

    def _consume_once(self, queue, on_message):
        method_frame, header_frame, body = self._channel.basic_get(queue)
        if method_frame:
            self._messages.add(method_frame.delivery_tag)
            future = self._pool.submit(on_message, body)
            future.add_done_callback(self._on_done(delivery_tag=method_frame.delivery_tag))

    def _on_done(self, delivery_tag):
        return lambda future: self._loop.call_soon(self._on_done_thread_safe, future, delivery_tag)

    def _on_done_thread_safe(self, future, delivery_tag):
        self._messages.remove(delivery_tag)
        result = future.result()

        if isinstance(result, Ack):
            self._channel.basic_ack(delivery_tag)
            # self._publish(result.message)
        elif isinstance(result, Nack):
            self._channel.basic_nack(delivery_tag, requeue=result.requeue)

        print(f'Tag={delivery_tag}, Result={result}')

    def _publish(self, message):
        self._channel.basic_publish(
            exchange='',
            routing_key='test',
            body=message)
