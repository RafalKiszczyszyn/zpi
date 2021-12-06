import feedparser
import requests
from datetime import datetime
from dependency_injector.wiring import inject, Provide
from typing import List
from zpi_common.services import loggers

from feedreader.core import core, tasks
from feedreader import containers
from feedreader.service import logic, models


class FeedReader(tasks.TaskExecutorBase):

    def __init__(
            self,
            tasks: List[tasks.ITask],
            publisher: logic.IFeedReaderLogic = Provide[containers.Container.feed_reader_logic],
            logger: loggers.ILogger = Provide[containers.Container.logger],
            *args, **kwargs):
        super().__init__(tasks)
        self._publisher = publisher
        self._logger = logger

    def before(self):
        self._logger.info(f'Starting execution of {len(self._tasks)} task(s).')

    def before_each(self, context: str):
        self._logger.info(f'Starting execution of {context}.')

    def handle_exception(self, context: str, e: Exception):
        self._logger.error(f'During execution of {context} an exception occurred:', e)

    def after_each(self, context: str, result):
        self._logger.info(f'Finished execution of {context}.')

    def after(self, results):
        self._logger.info(
            f'Finished execution of {self.tasks_count} task(s). '
            f'{len(results)} succeeded, {self.tasks_count - len(results)} failed.')

        feed = [result for _, result in results]
        self._publisher.publish_feed(feed)


class TaskStepBase(tasks.ITaskStep):

    @inject
    def __init__(self,
                 context,
                 logger: loggers.ILogger = Provide[containers.Container.logger],
                 *args, **kwargs):
        self._context = context
        self._logger = logger

    @property
    def context(self) -> str:
        return self._context

    def execute(self, data):
        pass

    def log(self, content):
        self._logger.info(f'({self.context}) {content}')


class RssParser(TaskStepBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = core.kwarg_lookup(kwargs, 'url', required=True)

    def execute(self, data):
        self.log(content=f"Parsing RSS from url={self.url}.")
        response = requests.get(self.url, headers={'User-Agent': 'FeedReader/0.1'})
        parsed = feedparser.parse(response.content)

        self.log(content=f"Parsed = {len(parsed.entries)} articles from '{parsed.feed.title}'. "
                 f"Last update: {parsed.feed.updated}.")

        return parsed


class RssConverter(TaskStepBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contentNodes = core.kwarg_lookup(kwargs, 'contentNodes', required=True)

    def execute(self, data):
        self.log(content='Converting RSS feed to consistent format.')

        channel = models.Channel(
            title=data['feed'].title,
            updated=self._datetime(data['feed'].updated_parsed),
            lang=data['feed'].language,
            contentNodes=self._contentNodes,
            articles=[]
        )

        for entry in data['entries']:
            channel.articles.append(self._map_article(entry))

        return channel

    @staticmethod
    def _map_article(entry):
        article = models.Article(
            title=entry.title,
            summary=entry.summary,
            published=RssConverter._datetime(entry.published_parsed),
            updated=RssConverter._datetime(entry.updated_parsed),
            link=entry.link,
            guid=entry.id,
            enclosures=[]
        )

        for entry_enclosure in [link for link in entry.links if link.rel == 'enclosure']:
            article.enclosures.append(RssConverter._map_enclosures(entry_enclosure))

        return article

    @staticmethod
    def _map_enclosures(entry_enclosure):
        enclosure = models.Enclosure(
            link=entry_enclosure.href,
            length=entry_enclosure.length,
            type=entry_enclosure.type
        )

        return enclosure

    @staticmethod
    def _datetime(date_parts):
        return datetime(
            year=date_parts[0],
            month=date_parts[1],
            day=date_parts[2],
            hour=date_parts[3],
            minute=date_parts[4],
            second=date_parts[5])
