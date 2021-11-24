import asyncio
import ssl
from abc import ABC, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import List, Union, Dict, Tuple

import pika

from .loggers import ILogger, DevNullLogger


class Response(ABC):
    pass


@dataclass(frozen=True)
class Ack(Response):
    message: Union[str, None] = None
    mandatory: bool = False


@dataclass(frozen=True)
class Nack(Response):
    requeue: bool


class IQueueController(ABC):

    @abstractmethod
    def consume(self, queue: str, message: str) -> Response:
        pass


class IQueueControllerFactory(ABC):

    @abstractmethod
    def create(self) -> IQueueController:
        pass


@dataclass(frozen=True)
class Binding:
    queue: str
    controller_factory: IQueueControllerFactory


@dataclass(frozen=True)
class Event:
    tag: int
    message: str = field(repr=False)


class IEventQueueConnection(ABC):

    @property
    @abstractmethod
    def queues(self) -> List[str]:
        pass

    @abstractmethod
    def publish(self, message: str, mandatory: bool):
        pass

    @abstractmethod
    def get(self, queue: str) -> Union[Event, None]:
        pass

    @abstractmethod
    def ack(self, event: Event):
        pass

    @abstractmethod
    def nack(self, event: Event, requeue: bool):
        pass

    @abstractmethod
    def close(self):
        pass


class IEventQueueClient(ABC):

    @abstractmethod
    def publish(self, message: str, mandatory: bool):
        pass

    @abstractmethod
    def consume(self, bindings: List[Binding]):
        pass

    @abstractmethod
    def disconnect(self):
        pass


# RabbitMQ Implementation

@dataclass
class RabbitMqExchange(ABC):
    name: str
    durable: bool = field(default=False)


@dataclass
class RabbitMqQueue:
    name: str
    exchange: str = field(default='')
    routing_key: str = field(default='')
    durable: bool = field(default=False)
    exclusive: bool = field(default=False)
    auto_delete: bool = field(default=False)


class RabbitMqConnection(IEventQueueConnection):

    def __init__(self,
                 fanout: str,
                 queues: Union[List[RabbitMqQueue], None] = None,
                 credentials: Union[Tuple[str, str], None] = None,
                 vhost: str = '/',
                 ssl_options: Union[ssl.SSLContext, None] = None,
                 logger: Union[ILogger, None] = None):
        credentials = credentials if credentials else ('guest', 'guest')

        self._fanout = fanout
        self._queues = queues
        self._ssl = ssl
        self._logger: ILogger = logger if logger else DevNullLogger()

        self._logger.info('Connecting with an event queue')
        self._connection = connection = pika.BlockingConnection(pika.ConnectionParameters(
                credentials=pika.PlainCredentials(username=credentials[0], password=credentials[1]),
                virtual_host=vhost,
                ssl_options=pika.SSLOptions(ssl_options)
        ))
        self._channel = connection.channel()
        self._channel.confirm_delivery()

        self._logger.info('Declaring exchange and queues')
        self._declare()

    @property
    def queues(self) -> List[str]:
        return [queue.name for queue in self._queues]

    def publish(self, message: str, mandatory: bool):
        self._channel.basic_publish(
            exchange=self._fanout,
            routing_key='',
            body=message.encode(encoding='utf-8'),
            mandatory=True)
        self._logger.info(f'Enqueued result on exchange={self._fanout}')

    def get(self, queue: str) -> Union[Event, None]:
        method_frame, header_frame, body = self._channel.basic_get(queue)
        if method_frame:
            return Event(method_frame.delivery_tag, body.decode('utf-8'))
        else:
            return None

    def ack(self, event: Event):
        self._channel.basic_ack(event.tag)

    def nack(self, event: Event, requeue: bool):
        self._channel.basic_nack(event.tag, requeue=requeue)

    def close(self):
        self._connection.close()

    def _declare(self):
        self._logger.info(f"Declaring fanout='{self._fanout}'")
        self._channel.exchange_declare(
            exchange=self._fanout,
            exchange_type='fanout')

        for queue in self._queues:
            self._logger.info(f'Declaring {queue}')
            self._channel.queue_declare(
                queue=queue.name,
                durable=queue.durable,
                exclusive=queue.exclusive,
                auto_delete=queue.auto_delete)

            if queue.exchange != '':
                self._channel.queue_bind(
                    queue=queue.name,
                    exchange=queue.exchange,
                    routing_key=queue.routing_key)


class EventQueueClient(IEventQueueClient):

    def __init__(self,
                 connection: IEventQueueConnection,
                 threads: int = 1,
                 messages_limit: int = 1,
                 logger: Union[ILogger, None] = None):
        self._is_stopped = False
        self._loop = asyncio.get_event_loop()

        self._connection = connection
        self._pool = ThreadPoolExecutor(threads)
        self._messages = set()
        self._msg_limit = messages_limit

        self._logger: ILogger = logger if logger else DevNullLogger()

    def publish(self, message: str, mandatory: bool):
        self._assert_is_not_stopped()
        self._connection.publish(message, mandatory)

    def consume(self, bindings: List[Binding]):
        self._assert_is_not_stopped()

        unavailable_queues = set([binding.queue for binding in bindings]) - set(self._connection.queues)
        if len(unavailable_queues) != 0:
            raise Exception(f'Queues={list(unavailable_queues)} are unavailable')

        try:
            self._loop.run_until_complete(self._consume(bindings))
        except Exception as e:
            self._logger.error('During consuming events an exception occurred', e)

    def disconnect(self):
        self._is_stopped = True
        self._connection.close()

    async def _consume(self, bindings: List[Binding]):
        self._logger.info(f'Started consuming events from queues={self._connection.queues}')
        while not self._is_stopped:
            if len(self._messages) < self._msg_limit:
                for binding in bindings:
                    self._consume_once(
                        queue=binding.queue,
                        controller=binding.controller_factory.create())
            await asyncio.sleep(0.1)

        self._logger.info('Stopped consuming events')
        self._connection.close()

    def _consume_once(self, queue: str, controller: IQueueController):
        event = self._connection.get(queue)
        if event:
            self._logger.info(
                f'Dequeued {event}, Controller={type(controller).__name__}')

            self._messages.add(event.tag)
            future = self._pool.submit(controller.consume, queue, event.message)
            future.add_done_callback(self._on_done(event=event))

    def _on_done(self, event: Event):
        return lambda future: self._loop.call_soon(self._on_done_thread_safe, future, event)

    def _on_done_thread_safe(self, future, event: Event):
        self._messages.remove(event.tag)
        result = future.result()

        self._logger.info(f'{event}, Result={type(result).__name__}')
        if isinstance(result, Ack):
            self._ack(result, event)
        elif isinstance(result, Nack):
            self._nack(result, event)

    def _ack(self, result: Ack, event: Event):
        self._connection.ack(event)
        if result.message is None:
            return

        try:
            self.publish(result.message, result.mandatory)
        except Exception as e:
            self._logger.error('During publishing result an exception occurred', e)
            self._connection.nack(event, requeue=True)
            self._logger.warning(f'Requeued {event}')
            self.disconnect()

    def _nack(self, result: Nack, event: Event):
        self._connection.nack(event, requeue=result.requeue)

    def _assert_is_not_stopped(self):
        if self._is_stopped:
            raise Exception('Event Queue Client is stopped')
