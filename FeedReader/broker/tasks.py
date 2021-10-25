import json
from datetime import datetime, timezone

import requests
from abc import abstractmethod, ABC

from rss_parser import Parser
import feedparser
from urllib3.exceptions import InsecureRequestWarning

from broker import core


class Task:

    class Meta:
        services = [core.InjectService(service_name='LOGGER', attribute_name='logger')]

    def __init__(self, context, steps):
        self.context = context
        self.steps = steps
        self.logger = None

    def log(self, content):
        if self.logger:
            self.logger.log(f'({self.context}) {content}')

    def execute(self):
        self.log('Started execution.')
        try:
            data = {}
            for step in self.steps:
                data = step.execute(data)
        except Exception as e:
            self.log(f'Error: {e}')
        self.log('Finished execution.')


class TaskStepBase(ABC):

    class Meta:
        services = [core.InjectService(service_name='LOGGER', attribute_name='logger')]

    def __init__(self, context, *args, **kwargs):
        self.context = context
        self.logger = None

    @abstractmethod
    def execute(self, data: dict) -> dict:
        pass

    def log(self, content):
        if self.logger:
            self.logger.log(f'({self.context}) {content}')


# ****************************************** IMPLEMENTATIONS ******************************************


class RssParser(TaskStepBase):

    class Meta:
        args = core.ConfigArgs(required=['url'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = None

    def execute(self, data: dict) -> dict:
        self.log(f"Parsing RSS from url={self.url}.")
        response = requests.get(self.url, headers={'User-Agent': 'FeedReader/0.1'})
        parsed = feedparser.parse(response.content)

        self.log(f"Parsed = {len(parsed.entries)} articles from '{parsed.feed.title}'. "
                 f"Last update: {parsed.feed.updated}.")

        return parsed


class RssMapper(TaskStepBase):

    def execute(self, data: dict) -> dict:
        self.log('Mapping RSS to consistent format.')

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

    class Meta:
        args = core.ConfigArgs(required=['channel'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = None

    def execute(self, data: dict) -> dict:
        raw = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        self.log(f'Publishing {len(raw.encode("utf-8"))} bytes of data on channel={self.channel}.')

        with open('feed.json', 'w', encoding='utf-8') as file:
            file.write(raw)

        return {}


class HttpGetTaskStep(TaskStepBase):

    class Meta:
        args = core.ConfigArgs(required=['url'], optional=['params', 'headers'])

    def __init__(self, *args, **kwargs):
        super(HttpGetTaskStep, self).__init__(*args, **kwargs)
        self.url = None
        self.params = None
        self.headers = None

    def execute(self, data: dict) -> dict:
        self.log(f"HTTP GET {self.url} with params: {self.params if self.params else 'None'}.")
        response = requests.get(self.url, params=self.params, headers=self.headers)
        self.log(f"Status = {response.status_code}. Fetched = {len(response.content)} bytes.")

        return response.json()


class HttpPostTaskStep(TaskStepBase):

    class Meta:
        args = core.ConfigArgs(required=['url'], optional=['params', 'headers'])

    def __init__(self, *args, **kwargs):
        super(HttpPostTaskStep, self).__init__(*args, **kwargs)
        self.url = None
        self.params = None
        self.headers = None

    def execute(self, data: dict) -> dict:
        self.log(f"HTTP POST {self.url} with "
                 f"params: {self.params if self.params else 'None'}, "
                 f"data: {data if data else 'None'}.")
        response = requests.post(self.url, json=data, params=self.params, headers=self.headers)
        self.log(f"Status = {response.status_code}. Fetched = {len(response.content)} bytes.")

        return response.json()
