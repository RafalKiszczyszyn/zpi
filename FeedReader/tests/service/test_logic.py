import dataclasses
import json
from datetime import datetime
from unittest import TestCase, mock
import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from zpi_common.services import events

from feedreader.service import models
from feedreader.service.logic import FeedReaderLogic


class FeedReaderLogicTests(TestCase):

    def test_PublishFeed_SomeArticlesAlreadyExist_OnlyNewArticlesArePublished(self):
        # Arrange:
        feed = [
            models.Channel(
                title="Channel1",
                updated=datetime.now(),
                lang="pl",
                contentNodes=[],
                articles=[
                    models.Article(
                        guid="ABC1",
                        title="Title1",
                        summary="Summary1",
                        published=datetime.now(),
                        updated=datetime.now(),
                        link="https://example.com",
                        enclosures=[]),
                    models.Article(
                        guid="ABC2",
                        title="Title2",
                        summary="Summary2",
                        published=datetime(2020, 10, 10),
                        updated=datetime.now(),
                        link="https://example.com",
                        enclosures=[])
                ]),
            models.Channel(
                title="Channel2",
                updated=datetime.now(),
                lang="pl",
                contentNodes=[],
                articles=[
                    models.Article(
                        guid="ABC3",
                        title="Title3",
                        summary="Summary3",
                        published=datetime.now(),
                        updated=datetime.now(),
                        link="https://example.com",
                        enclosures=[]),
                    models.Article(
                        guid="ABC4",
                        title="Title4",
                        summary="Summary4",
                        published=datetime(2020, 10, 10),
                        updated=datetime.now(),
                        link="https://example.com",
                        enclosures=[])
                ])
        ]
        newIds = ["ABC2", "ABC3"]
        expectedPublishedFeed = [
            models.Channel(
                title=feed[0].title,
                updated=feed[0].updated,
                lang=feed[0].lang,
                contentNodes=feed[0].contentNodes,
                articles=feed[0].articles[1:]
            ),
            models.Channel(
                title=feed[1].title,
                updated=feed[1].updated,
                lang=feed[1].lang,
                contentNodes=feed[1].contentNodes,
                articles=feed[1].articles[:1]
            ),
        ]

        repoMock = mock.MagicMock()
        repoMock.filter_existing.return_value = newIds

        connFactoryMock = mock.MagicMock()

        sut = FeedReaderLogic(
            articles_repository=repoMock,
            event_queue_connection_factory=connFactoryMock,
            logger=mock.MagicMock(),
            email_service=mock.MagicMock())

        # Act
        sut.publish_feed(feed)

        # Assert
        repoMock.save.assert_called_once_with(
            articles=expectedPublishedFeed[0].articles + expectedPublishedFeed[1].articles)

        for channel in expectedPublishedFeed:
            raw = json.dumps(dataclasses.asdict(channel), ensure_ascii=False, default=self._json_serialize)
            connFactoryMock.create().publisher().publish.assert_any_call(
                message=events.Message(body=raw, mandatory=True, persistence=False))

    @staticmethod
    def _json_serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)
