import dataclasses
import json
from typing import List

from dependency_injector.wiring import Provide, inject
from zpi_common.services import events, loggers
from zpi_common.services.events import Event, Result

from wordnet.service import models
from wordnet.nlp import nlp


def response(event: events.Event, segments: List[models.Segment]) -> events.Result:
    _segments = []
    for segment in segments:
        _segments.append(dataclasses.asdict(segment))
    raw = json.dumps(_segments, ensure_ascii=False)
    return events.Accept(event=event, message=raw)


class DebuggingQueueHandler(events.IEventHandler):

    def handle(self, event: Event) -> Result:
        print(event, event.body)
        return events.Accept(event)


class FeedQueueHandler(events.IEventHandler):

    @inject
    def __init__(self,
                 nlp_service: nlp.INlpService = Provide[nlp.INlpService.__name__],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        self._nlp = nlp_service
        self._logger = logger

    def handle(self, event: Event) -> Result:
        feed = json.loads(event.body)

        articles = []
        texts = []
        try:
            for entry in feed['articles']:
                guid = entry['guid']
                title = entry['title']
                texts.append(title)
                summary = entry['summary']
                texts.append(summary)
                article = models.Article(id=guid, title=title, summary=summary)
                articles.append(article)
        except KeyError as e:
            self._logger.error('Invalid event body', e)
            return events.Reject(event, requeue=False)

        polarities = self._nlp.polarity(texts)

        segments = []
        polarity = iter(polarities)
        for article in articles:
            title = models.Segment(id=article.id, segment='title', polarity=next(polarity))
            segments.append(title)
            summary = models.Segment(id=article.id, segment='summary', polarity=next(polarity))
            segments.append(summary)

        return response(event, segments)


class ScrapsQueueHandler(events.IEventHandler):

    @inject
    def __init__(self,
                 nlp_service: nlp.INlpService = Provide[nlp.INlpService.__name__],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        self._nlp = nlp_service
        self._logger = logger

    def handle(self, event: Event) -> Result:
        feed = json.loads(event.body)

        articles = []
        texts = []
        try:
            for entry in feed['articles']:
                guid = entry['guid']
                content = entry['content']
                texts.append(content)
                article = models.ScrappedArticle(id=guid, content=content)
                articles.append(article)
        except KeyError as e:
            self._logger.error('Invalid event body', e)
            return events.Reject(event, requeue=False)

        polarities = self._nlp.polarity(texts)

        segments = []
        for article, polarity in zip(articles, polarities):
            content = models.Segment(id=article.id, segment='content', polarity=polarity)
            segments.append(content)

        return response(event, segments)
