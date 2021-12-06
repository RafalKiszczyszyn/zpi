import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Union, List

from zpi_common.services import events
import pika
from zpi_common.services.events import Event, Message, IChannel, IConnection


class OperationProhibited(Exception):
    pass


class RabbitMqChannel(events.IChannel):

    def __init__(self, channel: pika.adapters.blocking_connection.BlockingChannel,
                 fanout: Union[str, None] = None,
                 queue: Union[str, None] = None,
                 mode: events.ChannelMode = events.ChannelMode.BIDIRECTIONAL):
        self._channel = channel
        self._fanout = fanout if fanout else ''
        self._queue = queue if queue else ''
        self._mode = mode

    @property
    def mode(self) -> events.ChannelMode:
        return self._mode

    @property
    def is_closed(self) -> bool:
        return self._channel.is_closed

    def publish(self, message: Message):
        self._assertIsOpen()
        self._assertPublishingIsAllowed()
        self._channel.basic_publish(
            exchange=self._fanout,
            routing_key='',
            body=message.body.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2 if message.persistence else 1),
            mandatory=message.mandatory)

    def consume(self) -> Iterable[Event]:
        self._assertIsOpen()
        self._assertConsumingIsAllowed()
        for frame, method, body in self._channel.consume(queue=self._queue, auto_ack=False):
            yield events.Event(topic=frame.exchange, tag=frame.delivery_tag, body=body.decode('utf-8'))

    def cancel(self):
        self._assertIsOpen()
        self._channel.cancel()

    def accept(self, event: events.Event):
        self._assertIsOpen()
        self._channel.basic_ack(delivery_tag=event.tag, multiple=False)

    def reject(self, event: events.Event, requeue: bool = False):
        self._assertIsOpen()
        self._channel.basic_reject(delivery_tag=event.tag, requeue=requeue)

    def close(self):
        if self._channel.is_open:
            self._channel.close()

    def _assertPublishingIsAllowed(self):
        if self.mode not in [events.ChannelMode.PUBLISHING, events.ChannelMode.BIDIRECTIONAL]:
            raise OperationProhibited(f'{type(self).__name__} is prohibited to publish')

    def _assertConsumingIsAllowed(self):
        if self.mode not in [events.ChannelMode.CONSUMING, events.ChannelMode.BIDIRECTIONAL]:
            raise OperationProhibited(f'{type(self).__name__} is prohibited to consume')

    def _assertIsOpen(self):
        if self._channel.is_closed:
            raise Exception(type(self).__name__ + ' is closed')


@dataclass
class FanoutConfig:
    name: str
    durable: bool = False
    auto_delete: bool = True


@dataclass
class QueueConfig:
    name: str
    durable: bool = False
    auto_delete: bool = False
    exclusive: bool = False


class IConfigProvider(ABC):

    @abstractmethod
    def queue(self) -> QueueConfig:
        pass

    @abstractmethod
    def fanout(self, topic: str) -> FanoutConfig:
        pass


class DefaultConfigProvider(IConfigProvider):

    def queue(self) -> QueueConfig:
        return QueueConfig(name='')

    def fanout(self, topic: str) -> FanoutConfig:
        return FanoutConfig(name=topic)


@dataclass
class RabbitMqConnectionParams:
    host: str
    vhost: str
    username: str
    password: str
    sslContext: Union[ssl.SSLContext, None] = None
    configProvider: IConfigProvider = field(default_factory=lambda: DefaultConfigProvider())


class RabbitMqConnection(events.IConnection):

    def __init__(self, connection: pika.BlockingConnection,
                 configProvider: Union[IConfigProvider, None] = None):
        self._connection = connection
        self._configProvider = configProvider if configProvider else DefaultConfigProvider()

    @property
    def is_closed(self) -> bool:
        return self._connection.is_closed

    def keep_alive(self):
        self._assert_is_open()
        self._connection.process_data_events()

    def close(self):
        if self._connection.is_open:
            self._connection.close()

    def publisher(self, topic: str) -> IChannel:
        self._assert_is_open()
        channel = self._connection.channel()
        channel.confirm_delivery()

        fanoutConfig = self._configProvider.fanout(topic)
        channel.exchange_declare(
            exchange=fanoutConfig.name,
            exchange_type='fanout',
            durable=fanoutConfig.durable,
            auto_delete=fanoutConfig.auto_delete)

        return RabbitMqChannel(
            channel=channel,
            fanout=fanoutConfig.name,
            mode=events.ChannelMode.PUBLISHING)

    def consumer(self, topics: List[str]) -> IChannel:
        self._assert_is_open()
        channel = self._connection.channel()
        channel.confirm_delivery()

        queueConfig = self._configProvider.queue()
        channel.queue_declare(
            queue=queueConfig.name,
            durable=queueConfig.durable,
            exclusive=queueConfig.exclusive,
            auto_delete=queueConfig.auto_delete)

        for topic in [topic for topic in topics if topic != '']:
            channel.queue_bind(
                queue=queueConfig.name,
                exchange=topic,
                routing_key='')

        return RabbitMqChannel(
            channel=channel,
            queue=queueConfig.name,
            mode=events.ChannelMode.CONSUMING)

    def _assert_is_open(self):
        if self._connection.is_closed:
            raise Exception(type(self).__name__ + ' is closed')


@dataclass(frozen=True)
class RabbitMqConnectionFactory(events.IConnectionFactory):
    params: RabbitMqConnectionParams

    def create(self) -> IConnection:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.params.host,
                virtual_host=self.params.vhost,
                credentials=pika.PlainCredentials(username=self.params.username, password=self.params.password),
                ssl_options=pika.SSLOptions(self.params.sslContext) if self.params.sslContext else None
            )
        )
        return RabbitMqConnection(
            connection=connection,
            configProvider=self.params.configProvider)
