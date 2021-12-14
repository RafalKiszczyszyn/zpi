import pathlib
import sys; sys.path.append(pathlib.Path(__file__).parent.parent.parent.resolve())

from unittest import TestCase, mock

from wordnet.service import events, bindings
from zpi_common.services import events as _events_


class DummyException(Exception):
    pass


def raiseException(*args, **kwargs):
    raise DummyException()


class EventDispatcherTests(TestCase):

    Topic = "topic"
    Message = "Hello World!"
    Event = _events_.Event(tag=1, body="", topic=Topic)

    @classmethod
    def getMocks(cls):
        return mock.MagicMock(), mock.MagicMock()

    def test_Dispatch_EventAcceptedWithMessage_ResponseIsPublished(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: _events_.Accept(event=e, message=self.Message)

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic=self.Topic, handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertTrue(result.isSuccess)
        publisherMock.publish.assert_called_once_with(
            _events_.Message(body=self.Message, mandatory=True, persistence=False))
        consumerMock.accept.assert_called_once_with(event=self.Event)

    def test_Dispatch_EventAcceptedWithMessageButPublisherRaisedAnException_EventIsRequeued(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: _events_.Accept(event=e, message=self.Message)

        consumerMock, publisherMock = self.getMocks()
        publisherMock.publish = raiseException

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic="topic", handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertFalse(result.isSuccess)
        self.assertTrue(result.error.isRuntime)
        self.assertIsInstance(result.error.exception, DummyException)

        consumerMock.accept.assert_not_called()
        consumerMock.reject.assert_called_once_with(event=self.Event, requeue=True)

    def test_Dispatch_EventAcceptedWithoutMessage_EventIsAccepted(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: _events_.Accept(event=e, message=None)

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic="topic", handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertTrue(result.isSuccess)
        consumerMock.accept.assert_called_once_with(event=self.Event)

    def test_Dispatch_EventRejectedWithReturning_EventIsRejected(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: _events_.Reject(event=e, requeue=True)

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic="topic", handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertFalse(result.isSuccess)
        self.assertTrue(result.error.isRuntime)
        self.assertIsNone(result.error.exception)
        consumerMock.reject.assert_called_once_with(event=self.Event, requeue=True)

    def test_Dispatch_EventRejectedWithoutReturning_EventIsRejected(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: _events_.Reject(event=e, requeue=False)

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic="topic", handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertTrue(result.isSuccess)
        consumerMock.reject.assert_called_once_with(event=self.Event, requeue=False)

    def test_Dispatch_HandlerRaisedException_EventIsRejected(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = raiseException

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic=self.Topic, handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertFalse(result.isSuccess)
        self.assertTrue(result.error.isRuntime)
        self.assertIsInstance(result.error.exception, DummyException)
        consumerMock.reject.assert_called_once_with(event=self.Event, requeue=True)

    def test_Dispatch_HandlerReturnedUnknownResponse_EventIsRejected(self):
        # Arrange
        handlerMock = mock.MagicMock()
        handlerMock.handle = lambda e: "Invalid Response"

        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic=self.Topic, handler=handlerMock)],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertFalse(result.isSuccess)
        self.assertFalse(result.error.isRuntime)
        self.assertIsNone(result.error.exception)

    def test_Dispatch_MissingBinding_EventIsRejected(self):
        # Arrange
        consumerMock, publisherMock = self.getMocks()

        sut = events.EventDispatcher(
            bindings=[bindings.Binding(topic="", handler=mock.MagicMock())],
            consumer=consumerMock,
            publisher=publisherMock)

        # Act
        result = sut.dispatch(self.Event)

        # Assert
        self.assertFalse(result.isSuccess)
        self.assertFalse(result.error.isRuntime)
        self.assertIsNone(result.error.exception)
        consumerMock.reject.assert_called_once_with(event=self.Event, requeue=True)
