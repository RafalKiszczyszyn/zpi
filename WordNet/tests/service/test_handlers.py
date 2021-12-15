import pathlib
import sys; sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))

import json
import random
from unittest import TestCase, mock

from zpi_common.services import events

from wordnet.service import models, handlers


def raiseException(*args, **kwargs):
    raise Exception


class ModuleTests(TestCase):

    def test_Response_SegmentsAreSerialisedAsJson(self):
        # Arrange
        event = events.Event(body="Hello World!", tag=1, topic="test")
        segments = [
            models.AnnotatedSegment(id="ABC123", segment=models.SegmentType.SUMMARY, polarity=-0.5)
        ]

        # Act
        response = handlers.response(event, segments)
        responseBody = json.loads(response.message)

        # Assert
        self.assertEqual(response.event, event)
        for segmentJson, segment in zip(responseBody, segments):
            self.assertEqual(segmentJson['id'], segment.id)
            self.assertEqual(segmentJson['segment'], segment.segment.value)
            self.assertEqual(segmentJson['polarity'], segment.polarity)


class EventHandlerTestsUtils:

    @staticmethod
    @mock.patch('json.loads')
    def Handle_InvalidEvent_Reject(jsonLoadMock, factoryMethod, case: TestCase):
        # Arrange
        event = mock.Mock()
        jsonLoadMock.return_value = {}

        # Act
        result = factoryMethod(nlp_service=mock.Mock(), logger=mock.Mock()).handle(event)

        # Assert
        case.assertIsInstance(result, events.Reject)
        case.assertEqual(result.event, event)
        case.assertFalse(result.requeue)

    @staticmethod
    @mock.patch('json.loads')
    def Handle_NlpFailure_Reject(jsonLoadMock, validEvent, factoryMethod, case: TestCase):
        # Arrange
        event = mock.Mock()
        jsonLoadMock.return_value = validEvent
        nlpServiceMock = mock.Mock()
        nlpServiceMock.polarity = raiseException

        # Act
        result = factoryMethod(nlp_service=nlpServiceMock, logger=mock.Mock()).handle(event)

        # Assert
        case.assertIsInstance(result, events.Reject)
        case.assertEqual(result.event, event)
        case.assertTrue(result.requeue)

    @staticmethod
    def Handle_ValidEvent_Accept(validEvent, segments, factoryMethod, case):
        # Arrange
        event = mock.Mock()
        polarities = [random.random() for _ in segments]
        nlpServiceMock = mock.Mock()
        nlpServiceMock.polarity.return_value = polarities

        # Act
        with mock.patch('json.loads') as jsonLoadMock:
            jsonLoadMock.return_value = validEvent
            result = factoryMethod(nlp_service=nlpServiceMock, logger=mock.Mock()).handle(event)

        # Assert
        case.assertIsInstance(result, events.Accept)
        case.assertEqual(result.event, event)
        responseBody = json.loads(result.message)
        for segmentJson, segment, polarity in zip(responseBody, segments, polarities):
            case.assertEqual(segmentJson['id'], segment["id"])
            case.assertEqual(segmentJson['polarity'], polarity)


class ScrapsEventHandlerTests(TestCase):

    ValidEvent = {
        "articles": [
            {"guid": "ABC123", "content": "Content"}
        ]
    }

    def test_Handle_InvalidEvent_Reject(self):
        EventHandlerTestsUtils.Handle_InvalidEvent_Reject(
            factoryMethod=lambda **kwargs: handlers.ScrapsEventHandler(**kwargs),
            case=self)

    def test_Handle_NlpFailure_Reject(self):
        EventHandlerTestsUtils.Handle_NlpFailure_Reject(
            validEvent=self.ValidEvent,
            factoryMethod=lambda **kwargs: handlers.ScrapsEventHandler(**kwargs),
            case=self)

    def test_Handle_ValidEvent_Accept(self):
        EventHandlerTestsUtils.Handle_ValidEvent_Accept(
            validEvent=self.ValidEvent,
            segments=[{"id": self.ValidEvent["articles"][0]["guid"]}],
            factoryMethod=lambda **kwargs: handlers.ScrapsEventHandler(**kwargs),
            case=self)


class FeedEventHandlerTests(TestCase):

    ValidEvent = {
        "articles": [
            {"guid": "ABC123", "title": "Title", "summary": "Summary"}
        ]
    }

    def test_Handle_InvalidEvent_Reject(self):
        EventHandlerTestsUtils.Handle_InvalidEvent_Reject(
            factoryMethod=lambda **kwargs: handlers.FeedEventHandler(**kwargs),
            case=self)

    def test_Handle_NlpFailure_Reject(self):
        EventHandlerTestsUtils.Handle_NlpFailure_Reject(
            validEvent=self.ValidEvent,
            factoryMethod=lambda **kwargs: handlers.FeedEventHandler(**kwargs),
            case=self)

    def test_Handle_ValidEvent_Accept(self):
        EventHandlerTestsUtils.Handle_ValidEvent_Accept(
            validEvent=self.ValidEvent,
            segments=[{"id": self.ValidEvent["articles"][0]["guid"]}, {"id": self.ValidEvent["articles"][0]["guid"]}],
            factoryMethod=lambda **kwargs: handlers.FeedEventHandler(**kwargs),
            case=self)


class DebuggingEventHandlerTests(TestCase):

    def test_Handle_ValidEvent_Accept(self):
        # Arrange
        event = mock.Mock()

        # Act
        result = handlers.DebuggingEventHandler().handle(event)

        # Assert
        self.assertIsInstance(result, events.Accept)
        self.assertEqual(result.event, event)
        self.assertIsNone(result.message)
