import dataclasses
import json
from enum import Enum
from typing import List

from dependency_injector.wiring import Provide, inject
from zpi_common.services import events, loggers
from zpi_common.services.events import Event, Result

from wordnet.service import models
from wordnet.nlp import nlp


def response(event: events.Event, segments: List[models.AnnotatedSegment]) -> events.Accept:
    def mapper(fields):
        mappedFields = {}
        for field in fields:
            name, value = field
            if issubclass(type(value), Enum):
                value = value.value
            mappedFields[name] = value
        return mappedFields

    _segments = []
    for segment in segments:
        _segments.append(dataclasses.asdict(segment, dict_factory=mapper))
    raw = json.dumps(_segments, ensure_ascii=False)

    return events.Accept(event=event, message=raw)


class DebuggingEventHandler(events.IEventHandler):

    def handle(self, event: Event) -> Result:
        print(event, event.body)
        return events.Accept(event)


class FeedEventHandler(events.IEventHandler):

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

        try:
            polarities = self._nlp.polarity(texts)
        except Exception as e:
            self._logger.error('Sentiment Analysis Service has thrown an exception', e)
            return events.Reject(event, requeue=True)

        segments = []
        polarity = iter(polarities)
        for article in articles:
            title = models.AnnotatedSegment(
                id=article.id, segment=models.SegmentType.TITLE, polarity=next(polarity))
            segments.append(title)

            summary = models.AnnotatedSegment(
                id=article.id, segment=models.SegmentType.SUMMARY, polarity=next(polarity))
            segments.append(summary)

        return response(event, segments)


class ScrapsEventHandler(events.IEventHandler):

    @inject
    def __init__(self,
                 nlp_service: nlp.INlpService = Provide[nlp.INlpService.__name__],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        self._nlp = nlp_service
        self._logger = logger

    def handle(self, event: Event) -> Result:
        scraps = json.loads(event.body)

        articles = []
        texts = []
        try:
            for entry in scraps['articles']:
                guid = entry['guid']
                content = entry['content']
                texts.append(content)
                article = models.ScrappedArticle(id=guid, content=content)
                articles.append(article)
        except KeyError as e:
            self._logger.error('Invalid event body', e)
            return events.Reject(event, requeue=False)

        try:
            polarities = self._nlp.polarity(texts)
        except Exception as e:
            self._logger.error('Sentiment Analysis Service has thrown an exception', e)
            return events.Reject(event, requeue=True)

        segments = []
        for article, polarity in zip(articles, polarities):
            content = models.AnnotatedSegment(
                id=article.id, segment=models.SegmentType.CONTENT, polarity=polarity)
            segments.append(content)

        return response(event, segments)
