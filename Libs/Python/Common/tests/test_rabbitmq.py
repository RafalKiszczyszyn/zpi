import pika
import pathlib
import sys; sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from unittest import TestCase, mock
from tests import utils

from zpi_common.services import events
from zpi_common.services.implementations.rabbitmq import RabbitMqConnection, FanoutConfig, QueueConfig, \
    RabbitMqChannel, OperationProhibited


# noinspection PyMethodMayBeStatic
class RabbitMqConnectionTests(TestCase):

    def test_IsClosed_ConnectionIsClosed_TrueIsReturned(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act
            result = sut.is_closed

            # Assert
            target.assert_called_once()
            self.assertTrue(result)

    def test_IsClosed_ConnectionIsOpen_FalseIsReturned(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act
            result = sut.is_closed

            # Assert
            target.assert_called_once()
            self.assertFalse(result)

    def test_KeepAlive_ConnectionIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act + Assert
            self.assertRaises(Exception, sut.keep_alive)
            connMock.process_data_events.assert_not_called()

    def test_KeepAlive_ConnectionIsOpen_ConnectionProcessDataEventsIsCalled(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act
            sut.keep_alive()

            # Assert
            target.assert_called_once()
            connMock.process_data_events.assert_called_once()

    def test_Close_ConnectionIsClosed_ConnectionCloseIsNotCalled(self):
        # Arrange
        with utils.mockProperty('is_open', False) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act
            sut.close()

            # Assert
            target.assert_called_once()
            connMock.close.assert_not_called()

    def test_Close_ConnectionIsOpen_ConnectionCloseIsCalled(self):
        # Arrange
        with utils.mockProperty('is_open', True) as (connMock, target):
            sut = RabbitMqConnection(connMock)

            # Act
            sut.close()

            # Assert
            target.assert_called_once()
            connMock.close.assert_called_once()

    def test_Publisher_ConnectionIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (connMock, target):
            topic = 'topic'
            sut = RabbitMqConnection(connMock)

            # Act + Assert
            self.assertRaises(Exception, sut.publisher, topic)
            connMock.channel.assert_not_called()

    @mock.patch('zpi_common.services.implementations.rabbitmq.RabbitMqChannel')
    def test_Publisher_ConnectionIsOpen_RabbitMqChannelIsCreated(self, channel):
        # Arrange
        with utils.mockProperty('is_closed', False) as (connMock, target):
            topic = 'topic'
            fanoutConfig = FanoutConfig(
                name=topic,
                durable=True,
                auto_delete=True
            )
            configProviderMock = mock.Mock()
            configProviderMock.fanout.return_value = fanoutConfig
            sut = RabbitMqConnection(connection=connMock, configProvider=configProviderMock)

            # Act
            sut.publisher(topic)

            # Assert
            connMock.channel.assert_called_once()
            connMock.channel().confirm_delivery.assert_called_once()
            connMock.channel().exchange_declare.assert_called_once_with(
                exchange=fanoutConfig.name,
                exchange_type='fanout',
                durable=fanoutConfig.durable,
                auto_delete=fanoutConfig.auto_delete
            )
            configProviderMock.fanout.assert_called_once_with(topic)
            channel.assert_called_once_with(
                channel=connMock.channel(),
                fanout=fanoutConfig.name,
                mode=events.ChannelMode.PUBLISHING)

    def test_Consumer_ConnectionIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (connMock, target):
            topics = ['topic1', 'topic2']
            sut = RabbitMqConnection(connMock)

            # Act + Assert
            self.assertRaises(Exception, sut.consumer, topics)
            connMock.channel.assert_not_called()

    @mock.patch('zpi_common.services.implementations.rabbitmq.RabbitMqChannel')
    def test_Consumer_ConnectionIsOpen_RabbitMqChannelIsCreated(self, channel):
        # Arrange
        with utils.mockProperty('is_closed', False) as (connMock, target):
            topics = ['topic1', '', 'topic2']
            queueConfig = QueueConfig(
                name='queue',
                durable=True,
                exclusive=True,
                auto_delete=True
            )
            configProviderMock = mock.Mock()
            configProviderMock.queue.return_value = queueConfig
            sut = RabbitMqConnection(connection=connMock, configProvider=configProviderMock)

            # Act
            sut.consumer(topics)

            # Assert
            connMock.channel.assert_called_once()
            connMock.channel().confirm_delivery.assert_called_once()
            configProviderMock.queue.assert_called_once()
            connMock.channel().queue_declare.assert_called_once_with(
                queue=queueConfig.name,
                durable=queueConfig.durable,
                exclusive=queueConfig.exclusive,
                auto_delete=queueConfig.auto_delete)

            # For each nonempty topic
            calls = []
            nonemptyTopics = [topic for topic in topics if topic != '']
            for topic in nonemptyTopics:
                call = mock.call(
                    queue=queueConfig.name,
                    exchange=topic,
                    routing_key='')
                calls.append(call)
            connMock.channel().queue_bind.has_calls(calls)
            self.assertEqual(connMock.channel().queue_bind.call_count, len(nonemptyTopics))

            channel.assert_called_once_with(
                channel=connMock.channel(),
                queue=queueConfig.name,
                mode=events.ChannelMode.CONSUMING)


# noinspection PyMethodMayBeStatic
class RabbitMqChannelTests(TestCase):

    def test_IsClosed_ChannelIsClosed_TrueIsReturned(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channel=channelMock)

            # Act
            result = sut.is_closed

            # Assert
            target.assert_called_once()
            self.assertTrue(result)

    def test_IsClosed_ChannelIsOpen_FalseIsReturned(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            sut = RabbitMqChannel(channel=channelMock)

            # Act
            result = sut.is_closed

            # Assert
            target.assert_called_once()
            self.assertFalse(result)

    def test_Close_ChannelIsClosed_ChannelCloseIsNotCalled(self):
        # Arrange
        with utils.mockProperty('is_open', False) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act
            sut.close()

            # Assert
            target.assert_called_once()
            channelMock.close.assert_not_called()

    def test_Close_ChannelIsOpen_ChannelCloseIsCalled(self):
        # Arrange
        with utils.mockProperty('is_open', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act
            sut.close()

            # Assert
            target.assert_called_once()
            channelMock.close.assert_called_once()

    def test_Publish_ChannelIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act + Assert
            self.assertRaises(Exception, sut.publish, message=mock.Mock())
            channelMock.basic_publish.assert_not_called()

    def test_Publish_ChannelIsProhibitedToPublish_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            sut = RabbitMqChannel(channelMock, mode=events.ChannelMode.CONSUMING)

            # Act + Assert
            self.assertRaises(OperationProhibited, sut.publish, message=mock.Mock())
            channelMock.basic_publish.assert_not_called()

    def test_Publish_ChannelIsAllowedToPublish_MessageIsPublished(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            fanout = 'topic'
            message1 = events.Message(
                body='Hello world!',
                mandatory=True,
                persistence=True)
            message2 = events.Message(
                body='Hello world!',
                mandatory=False,
                persistence=False)
            sut = RabbitMqChannel(channelMock, fanout=fanout, mode=events.ChannelMode.BIDIRECTIONAL)

            # Act
            sut.publish(message1)
            sut.publish(message2)

            # Assert
            channelMock.basic_publish.assert_has_calls([
                mock.call(
                    exchange=fanout,
                    routing_key='',
                    body=message1.body.encode('utf-8'),
                    properties=pika.BasicProperties(delivery_mode=2),
                    mandatory=message1.mandatory),
                mock.call(
                    exchange=fanout,
                    routing_key='',
                    body=message2.body.encode('utf-8'),
                    properties=pika.BasicProperties(delivery_mode=1),
                    mandatory=message2.mandatory)])

    def test_Consume_ChannelIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act + Assert
            self.assertRaises(Exception, next, iter(sut.consume()))
            channelMock.consume.assert_not_called()

    def test_Consume_ChannelIsProhibitedToPublish_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            sut = RabbitMqChannel(channelMock, mode=events.ChannelMode.PUBLISHING)

            # Act + Assert
            self.assertRaises(OperationProhibited, next, iter(sut.consume()))
            channelMock.consume.assert_not_called()

    def test_Consume_ChannelIsAllowedToConsume_EventIsReturned(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            queue = 'queue'
            frameMock, methodMock, bodyMock = mock.Mock(), mock.Mock(), mock.Mock()
            channelMock.consume.return_value = [(frameMock, methodMock, bodyMock)]
            sut = RabbitMqChannel(channelMock, queue=queue, mode=events.ChannelMode.BIDIRECTIONAL)

            # Act
            _events = iter(sut.consume())
            event = next(_events)

            # Assert
            self.assertEqual(event.topic, frameMock.exchange)
            self.assertEqual(event.body, bodyMock.decode('utf-8'))
            self.assertEqual(event.tag, frameMock.delivery_tag)
            self.assertRaises(StopIteration, next, _events)

    def test_Cancel_ChannelIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act + Assert
            self.assertRaises(Exception, sut.cancel)
            channelMock.cancel.assert_not_called()

    def test_Cancel_ChannelIsOpen_ChannelCancelIsCalled(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act
            sut.cancel()

            # Assert
            channelMock.cancel.assert_called_once()

    def test_Accept_ChannelIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act + Assert
            self.assertRaises(Exception, sut.accept, event=mock.Mock())
            channelMock.basic_ack.assert_not_called()

    def test_Accept_ChannelIsOpen_ChannelBasicAckIsCalled(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            event = events.Event(topic='topic', tag=1, body='Hello world!')
            sut = RabbitMqChannel(channelMock)

            # Act
            sut.accept(event)

            # Assert
            channelMock.basic_ack.assert_called_once_with(delivery_tag=event.tag, multiple=False)

    def test_Reject_ChannelIsClosed_ExceptionIsRaised(self):
        # Arrange
        with utils.mockProperty('is_closed', True) as (channelMock, target):
            sut = RabbitMqChannel(channelMock)

            # Act + Assert
            self.assertRaises(Exception, sut.reject, event=mock.Mock(), requeue=False)
            channelMock.basic_nack.assert_not_called()

    def test_Reject_ChannelIsOpen_ChannelBasicNackIsCalled(self):
        # Arrange
        with utils.mockProperty('is_closed', False) as (channelMock, target):
            event = events.Event(topic='topic', tag=1, body='Hello world!')
            sut = RabbitMqChannel(channelMock)

            # Act
            sut.reject(event, requeue=True)

            # Assert
            channelMock.basic_reject.assert_called_once_with(delivery_tag=event.tag, requeue=True)
