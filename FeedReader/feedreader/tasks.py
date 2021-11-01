import json
import feedparser
import requests
from datetime import datetime
from abc import abstractmethod, ABC
from dependency_injector.wiring import inject, Provide

from feedreader import core, containers, loggers, workers


class TaskBuilder:

    def __init__(self, implementation_builder: core.AbstractImplementationBuilder):
        if not issubclass(type(implementation_builder), core.AbstractImplementationBuilder):
            raise TypeError('Parameter implementation_builder '
                            'must be an implementation of AbstractImplementationBuilder.')
        self.implementation_builder = implementation_builder

    def build(self, config):
        if 'name' not in config:
            raise Exception('No task name specified.')
        if 'steps' not in config:
            raise Exception('No task steps specified.')

        context = f"Task='{config['name']}'"
        steps = []
        try:
            for config_step in config['steps']:
                step = self._build_task_step(config_step, context)
                steps.append(step)
        except Exception as e:
            raise Exception(f'Loading task step failed with message: {e}')

        task = Task(context, steps)
        return task

    def _build_task_step(self, config, context):
        if 'name' not in config:
            raise Exception('No task step name specified.')

        context = f"{context}, Step='{config['name']}'"
        try:
            implementation = self.implementation_builder.build(config, context=context)
            if not issubclass(type(implementation), TaskStepBase):
                raise Exception('Task step implementation must be a subclass of TaskStepBase.')
            return implementation
        except Exception as e:
            raise Exception(f'Loading task step implementation failed with message: {e}')


class Task:

    @inject
    def __init__(self, context, steps):
        self.context = context
        self.steps = steps

    @inject
    def log(self, content, logger: loggers.LoggerBase = Provide[containers.Container.logger]):
        logger.log(f'({self.context}) {content}')

    def execute(self):
        self.log(content='Started execution.')
        try:
            data = {}
            for step in self.steps:
                data = step.execute(data)
        except Exception as e:
            self.log(f'Error: {e}')
        self.log('Finished execution.')


class TaskStepBase(ABC):

    def __init__(self, context, *args, **kwargs):
        self.context = context

    @abstractmethod
    def execute(self, data: dict) -> dict:
        pass

    @inject
    def log(self, content, logger: loggers.LoggerBase = Provide[containers.Container.logger]):
        logger.log(f'({self.context}) {content}')


# ****************************************** IMPLEMENTATIONS ******************************************


class RssParser(TaskStepBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = core.kwarg_lookup(kwargs, 'url', required=True)

    def execute(self, data: dict) -> dict:
        self.log(content=f"Parsing RSS from url={self.url}.")
        response = requests.get(self.url, headers={'User-Agent': 'FeedReader/0.1'})
        parsed = feedparser.parse(response.content)

        self.log(content=f"Parsed = {len(parsed.entries)} articles from '{parsed.feed.title}'. "
                 f"Last update: {parsed.feed.updated}.")

        return parsed


class RssMapper(TaskStepBase):

    def execute(self, data: dict) -> dict:
        self.log(content='Mapping RSS to consistent format.')

        mapped = {
            'title': data['feed'].title,
            'updated': self.datetime(data['feed'].updated_parsed),
            'lang': data['feed'].language,
            'articles': []
        }

        for article in data['entries']:
            mapped['articles'].append(self._map_article(article))

        return mapped

    @staticmethod
    def _map_article(article):
        mapped = {
            'title': article.title,
            'summary': article.summary,
            'published': RssMapper.datetime(article.published_parsed),
            'updated': RssMapper.datetime(article.updated_parsed),
            'link': article.link,
            'guid': article.id,
            'enclosures': []
        }

        for enclosure in [link for link in article.links if link.rel == 'enclosure']:
            mapped['enclosures'].append(RssMapper._map_enclosures(enclosure))

        return mapped

    @staticmethod
    def _map_enclosures(enclosure):
        mapped = {
            'link': enclosure.href,
            'length': enclosure.length,
            'type': enclosure.type
        }

        return mapped

    @staticmethod
    def datetime(date_parts):
        return datetime(
            year=date_parts[0],
            month=date_parts[1],
            day=date_parts[2],
            hour=date_parts[3],
            minute=date_parts[4],
            second=date_parts[5]).isoformat()


class QueueEventPublisher(TaskStepBase):

    @inject
    def __init__(self,
                 dispatcher: workers.BackgroundJobDispatcher = Provide[containers.Container.dispatcher],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = core.kwarg_lookup(kwargs, 'channel', required=True)
        self._dispatcher = dispatcher

    def execute(self, data: dict) -> dict:
        raw = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        self.log(content=f'Publishing {len(raw.encode("utf-8"))} bytes of data on channel={self.channel}.')

        job = workers.EventQueueBackgroundJob(
            name=self.context,
            channel=self.channel,
            content=raw)

        self._dispatcher.enqueue_job(job)

        return {}
