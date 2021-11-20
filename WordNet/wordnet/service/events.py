import asyncio
import pika
from dataclasses import dataclass, field
from typing import List
from concurrent.futures import ThreadPoolExecutor
from wordnet.core import events, bindings as _bindings_, loggers, controllers


@dataclass
class RabbitMqQueue(events.IQueue):
    exchange: str
    routing_key: str = field(default='')
    durable: bool = field(default=False)
    exclusive: bool = field(default=False)
    auto_delete: bool = field(default=False)


class RabbitMqConsumer(events.IQueueConsumer):

    # noinspection PyTypeChecker
    def __init__(self, bindings: List[_bindings_.Binding],
                 logger: loggers.ILogger,
                 exchange,
                 threads,
                 messages_limit):
        self._is_running = True
        self._loop = asyncio.get_event_loop()

        self._bindings = bindings
        self._logger = logger

        self._connection: pika.adapters.blocking_connection.BlockingConnection = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel = None
        self._exchange = exchange

        self._pool = ThreadPoolExecutor(threads)
        self._messages = set()
        self._msg_limit = messages_limit

    def consume(self):
        self._logger.info('Connecting with an event queue')
        self._connection = connection = pika.BlockingConnection()
        self._is_running = True

        self._channel = connection.channel()
        self._channel.confirm_delivery()
        self._channel.exchange_declare(
            exchange=self._exchange,
            exchange_type='fanout')
        self._declare_queues()

        try:
            self._loop.run_until_complete(self._consume())
        except Exception as e:
            self._logger.error('During consuming events, exception occurred', e)

    def stop(self):
        self._is_running = False

    def _declare_queues(self):
        for binding in self._bindings:
            if not isinstance(binding.queue, RabbitMqQueue):
                raise Exception(f'Binding={binding.queue} must be type of {RabbitMqQueue.__name__}')
            queue: RabbitMqQueue = binding.queue

            self._logger.info(f'Declaring queue={queue.name}')
            self._channel.queue_declare(
                queue=queue.name,
                durable=queue.durable,
                exclusive=queue.exclusive,
                auto_delete=queue.auto_delete)

            if queue.exchange != '':
                self._logger.info(
                    f'Binding queue={queue.name} with exchange={queue.exchange} '
                    f'using routing key={queue.routing_key}')
                self._channel.queue_bind(
                    queue=queue.name,
                    exchange=queue.exchange,
                    routing_key=queue.routing_key)

    async def _consume(self):
        self._logger.info('Started consuming events')
        while self._is_running:
            if len(self._messages) < self._msg_limit:
                for binding in self._bindings:
                    self._consume_once(
                        queue=binding.queue.name,
                        controller=binding.controller_factory())
            await asyncio.sleep(0.1)

        self._logger.info('Stopped consuming events')
        self._connection.close()
        self._loop.stop()

    def _consume_once(self, queue: str, controller: controllers.IQueueController):
        method_frame, header_frame, body = self._channel.basic_get(queue)
        if method_frame:
            self._logger.info(
                f'Dequeued Event(tag={method_frame.delivery_tag}), Controller={type(controller).__name__}')

            self._messages.add(method_frame.delivery_tag)
            future = self._pool.submit(controller.consume, body.decode('utf-8'))
            future.add_done_callback(self._on_done(delivery_tag=method_frame.delivery_tag))

    def _on_done(self, delivery_tag: int):
        return lambda future: self._loop.call_soon(self._on_done_thread_safe, future, delivery_tag)

    def _on_done_thread_safe(self, future, delivery_tag: int):
        self._messages.remove(delivery_tag)
        result = future.result()

        self._logger.info(f'Event(tag={delivery_tag}), Result={type(result).__name__}')
        if isinstance(result, events.Ack):
            self._ack(result, delivery_tag)
        elif isinstance(result, events.Nack):
            self._nack(result, delivery_tag)

    def _ack(self, result: events.Ack, delivery_tag: int):
        try:
            # self._publish(result.message)
            self._channel.basic_ack(delivery_tag)
        except Exception as e:
            self._logger.error('During publishing result an exception occurred', e)
            self._channel.basic_nack(delivery_tag, requeue=True)
            self._logger.warning(f'Requeued Event(tag={delivery_tag})')
            self.stop()

    def _nack(self, result: events.Nack, delivery_tag: int):
        self._channel.basic_nack(delivery_tag, requeue=result.requeue)

    def _publish(self, message: str):
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key='',
            body=message.encode(encoding='utf-8'),
            mandatory=True)
        self._logger.info(f'Enqueued result on exchange={self._exchange}')
