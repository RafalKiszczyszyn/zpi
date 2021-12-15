import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from unittest import TestCase, mock
from unittest.mock import patch

from feedreader.service import models
from feedreader.service.tasks import RssParser, RssConverter, FeedReader


class RssParserTests(TestCase):

    @patch('feedparser.parse')
    @patch('requests.get')
    def test_Execute_ParsedDataIsReturned(self, requestMock, parserMock):
        # Arrange
        contentMock = mock.Mock()
        contentMock.content = 'Content'
        requestMock.return_value = contentMock

        resultMock = mock.Mock()
        resultMock.entries = []
        parserMock.return_value = resultMock

        # Act
        parsed = RssParser(context="Context", url='http://example.com').execute({})

        # Assert
        self.assertEqual(parsed, resultMock)
        self.assertEqual(requestMock.call_count, 1)
        parserMock.assert_called_once_with("Content")


class RssConverterTests(TestCase):

    def test_Execute_ChannelIsReturned(self):
        # Arrange
        feedMock = mock.Mock()
        feedMock.updated_parsed = [2021, 12, 12, 00, 00, 00]

        enclosureMock = mock.Mock()
        enclosureMock.rel = 'enclosure'

        entryMock = mock.Mock()
        entryMock.published_parsed = [2021, 12, 12, 00, 00, 00]
        entryMock.updated_parsed = [2021, 12, 12, 00, 00, 00]
        entryMock.links = [enclosureMock, mock.Mock()]
        data = {
            "feed": feedMock,
            "entries": [entryMock]
        }

        # Act
        channel = RssConverter(context='Context', contentNodes=['ContentNodes']).execute(data)

        # Assert
        self.assertTrue(isinstance(channel, models.Channel))


class FeedReaderTests(TestCase):

    def test_Execute_PublisherIsCalled(self):
        # Arrange
        taskMock = mock.Mock()
        taskResultMock = mock.Mock()
        taskMock.execute.return_value = taskResultMock
        publisherMock = mock.Mock()

        # Act
        FeedReader(tasks=[taskMock], publisher=publisherMock, logger=mock.Mock()).execute()

        # Assert
        publisherMock.publish_feed.assert_called_once_with([taskResultMock])
        self.assertTrue(True)
