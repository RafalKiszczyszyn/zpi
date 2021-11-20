import dataclasses
import json
from typing import List

from dependency_injector.wiring import Provide, inject

from wordnet.core import controllers, events, loggers
from wordnet.service import models
from wordnet.nlp import sentiments


def response(segments: List[models.Segment]) -> events.Response:
    _segments = []
    for segment in segments:
        _segments.append(dataclasses.asdict(segment))
    raw = json.dumps(_segments, ensure_ascii=False)
    return events.Ack(raw)


class TestQueueController(controllers.IQueueController):

    @inject
    def __init__(self,
                 pipeline: sentiments.INlpPipeline = Provide[f"nlp.{sentiments.INlpPipeline.__name__}"]):
        self._pipeline = pipeline

    def consume(self, message: str) -> events.Response:
        print(self._pipeline.retrieve_sentiments([message]))
        return events.Ack('Done!')


class FeedQueueController(controllers.IQueueController):

    @inject
    def __init__(self,
                 pipeline: sentiments.INlpPipeline = Provide[f"nlp.{sentiments.INlpPipeline.__name__}"],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        self._pipeline = pipeline
        self._logger = logger

    def consume(self, message: str) -> events.Response:
        feed = json.loads(message)

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
            return events.Nack(requeue=False)

        sentiments_ = self._pipeline.retrieve_sentiments(texts)

        segments = []
        sentiment = iter(sentiments_)
        for article in articles:
            title = models.Segment(id=article.id, segment='title', sentiment=next(sentiment))
            segments.append(title)
            summary = models.Segment(id=article.id, segment='summary', sentiment=next(sentiment))
            segments.append(summary)

        return response(segments)
