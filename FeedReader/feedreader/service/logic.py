import dataclasses
import json
from abc import abstractmethod, ABC
from datetime import datetime
from traceback import TracebackException
from typing import List, Dict, Tuple, Iterable, Union
from zpi_common.services import loggers, events, notifications

from feedreader.service import persistance, models


class IFeedReaderLogic(ABC):

    @abstractmethod
    def publish_feed(self, feed: List[models.Channel]):
        pass


class FeedReaderLogic(IFeedReaderLogic):

    class InnerException(Exception):
        pass

    def __init__(self,
                 articles_repository: persistance.IArticlesRepository,
                 event_queue_connection_factory: events.IConnectionFactory,
                 logger: loggers.ILogger,
                 email_service: notifications.IEmailBroadcastService):
        self._repository = articles_repository
        self._conn_factory = event_queue_connection_factory
        self._logger = logger
        self._email_service = email_service

    def publish_feed(self, feed: List[models.Channel]):
        try:
            self._publish_feed(feed=feed)
        except FeedReaderLogic.InnerException:
            self._logger.warning(warning='Feed was neither send nor saved.')
        except Exception as e:
            self._logger.error(message='Unexpected exception in logic', error=e)

    def _publish_feed(self, feed: List[models.Channel]):
        articles_mapped_to_channels = self._create_articles_to_channels_map(feed=feed)
        ids = self._get_ids(feed=feed)
        new_ids = self._filter_existing_ids(ids=ids)

        new_feed = set()
        articles = list()
        for new_id in new_ids:
            (new_channel, article) = articles_mapped_to_channels[new_id]
            new_channel.articles.append(article)

            new_feed.add(new_channel)
            articles.append(article)

        self._publish_events(new_feed)
        self._save_new_articles(articles)

    def _filter_existing_ids(self, ids: List[str]) -> List[str]:
        try:
            new_ids = self._repository.filter_existing(ids=ids)
            self._logger.info(f'Found {len(ids) - len(new_ids)} existing articles.')
            return new_ids
        except Exception as e:
            self._exc(info='During retrieving articles ids an exception was thrown:', e=e)

    def _save_new_articles(self, articles: List[models.Article]):
        try:
            self._logger.info(f'Saving {len(articles)} new articles.')
            self._repository.save(articles=articles)
        except Exception as e:
            self._exc(info='During saving new articles an exception was thrown:', e=e)

    def _publish_events(self, feed: Iterable[models.Channel]):
        connection: Union[events.IConnection, None] = None
        try:
            connection = self._conn_factory.create()
            publisher = connection.publisher(topic='feed')
            for channel in feed:
                if len(channel.articles) == 0:
                    continue

                self._logger.info(
                    f"Sending event with feed from source='{channel.title}' "
                    f"and {len(channel.articles)} new articles.")
                raw = json.dumps(dataclasses.asdict(channel), ensure_ascii=False, default=self._json_serialize)
                publisher.publish(message=events.Message(body=raw, mandatory=True, persistence=False))
        except Exception as e:
            self._exc(info='During publishing events an exception was thrown:', e=e)
        finally:
            if connection and not connection.is_closed:
                connection.close()

    def _exc(self, info: str, e: Exception):
        self._logger.error(message=info, error=e)
        self._send_email(info=info, e=e)
        raise FeedReaderLogic.InnerException()

    def _send_email(self, info: str, e: Exception):
        if self._email_service is None:
            return
        try:
            traceback = "".join(TracebackException.from_exception(e).format())
            self._email_service.error('Exception notified in Feed Reader', message=info, traceback=traceback)
        except Exception as e:
            self._logger.error(message='During sending an email exception was thrown:', error=e)

    @staticmethod
    def _create_articles_to_channels_map(feed: List[models.Channel]) \
            -> Dict[str, Tuple[models.Channel, models.Article]]:
        articles_mapped_to_channels = {}
        for channel in feed:
            new_channel = models.Channel(
                title=channel.title,
                updated=channel.updated,
                lang=channel.lang,
                contentNodes=channel.contentNodes,
                articles=[])
            for article in channel.articles:
                articles_mapped_to_channels[article.guid] = (new_channel, article)
        return articles_mapped_to_channels

    @staticmethod
    def _get_ids(feed: List[models.Channel]) -> List[str]:
        ids = []
        for channel in feed:
            for article in channel.articles:
                ids.append(article.guid)
        return ids

    @staticmethod
    def _json_serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)
