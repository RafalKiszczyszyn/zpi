import dataclasses
import json
from abc import abstractmethod, ABC
from datetime import datetime
from traceback import TracebackException
from typing import List, Dict, Tuple, Iterable

from feedreader.app import persistance, events, loggers, notifications, models


class IFeedReaderLogic(ABC):

    @abstractmethod
    def publish_feed(self, feed: List[models.Channel]):
        pass


# noinspection PyBroadException
class FeedReaderLogic(IFeedReaderLogic):

    class InnerException(Exception):
        pass

    def __init__(self,
                 articles_repository: persistance.IArticlesRepository,
                 event_publisher: events.IEventQueuePublisher,
                 logger: loggers.LoggerBase,
                 email_service: notifications.IEmailService):
        self._repository = articles_repository
        self._publisher = event_publisher
        self._logger = logger
        self._email_service = email_service

    def publish_feed(self, feed: List[models.Channel]):
        try:
            self._publish_feed(feed=feed)
        except FeedReaderLogic.InnerException:
            self._logger.log(content='Feed was neither send nor saved.')
        except Exception as e:
            self._logger.log_error(info='Unexpected exception in logic:', e=e)

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
            articles.append(persistance.ArticleDao(id=new_id, published=article.published))

        self._publish_events(new_feed)
        self._save_new_articles(articles)

    def _filter_existing_ids(self, ids: List[str]) -> List[str]:
        try:
            new_ids = self._repository.filter_existing(ids=ids)
            self._logger.log(content=f'Found {len(ids) - len(new_ids)} existing articles.')
            return new_ids
        except Exception as e:
            self._exc(info='During retrieving articles ids an exception was thrown:', e=e)

    def _save_new_articles(self, articles: List[persistance.ArticleDao]):
        try:
            self._logger.log(content=f'Saving {len(articles)} new articles.')
            self._repository.save(articles=articles)
        except Exception as e:
            self._exc(info='During saving new articles an exception was thrown:', e=e)

    def _publish_events(self, feed: Iterable[models.Channel]):
        try:
            self._publisher.connect()
            for channel in feed:
                if len(channel.articles) == 0:
                    continue

                self._logger.log(
                    content=f"Sending event with feed from source='{channel.source}' "
                            f"and {len(channel.articles)} new articles.")
                raw = json.dumps(dataclasses.asdict(channel), ensure_ascii=False, default=self._json_serialize)
                self._publisher.publish(channel='feed', message=raw)
        except Exception as e:
            self._exc(info='During publishing events an exception was thrown:', e=e)
        finally:
            self._publisher.close()

    def _exc(self, info: str, e: Exception):
        self._logger.log_error(info=info, e=e)
        self._send_email(info=info, e=e)
        raise FeedReaderLogic.InnerException()

    def _send_email(self, info: str, e: Exception):
        if self._email_service is None:
            return
        try:
            traceback = "".join(TracebackException.from_exception(e).format())
            self._email_service.broadcast('Exception notified in Feed Reader', info=info, traceback=traceback)
        except Exception as e:
            self._logger.log_error(info='During sending an email exception was thrown:', e=e)

    @staticmethod
    def _create_articles_to_channels_map(feed: List[models.Channel]) \
            -> Dict[str, Tuple[models.Channel, models.Article]]:
        articles_mapped_to_channels = {}
        for channel in feed:
            new_channel = models.Channel(
                source=channel.source,
                title=channel.title,
                updated=channel.updated,
                lang=channel.lang,
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
