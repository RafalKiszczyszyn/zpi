from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import spacy

from . import persistence, models


class INlpPipeline(ABC):

    @abstractmethod
    def retrieve_sentiments(self, texts: List[str]):
        pass


class SpacyPipeline(INlpPipeline):

    def __init__(self, repository: persistence.ISentimentAnnotationsRepository):
        self._repo = repository

        nlp = spacy.load("pl_core_news_sm")
        disabled = set(nlp.component_names) - {'tok2vec', 'morphologizer', 'tagger', 'lemmatizer'}
        nlp.select_pipes(
            disable=disabled)
        self._nlp = nlp

    def retrieve_sentiments(self, texts: List[str]) -> List[int]:
        docs = list(self._nlp.pipe(texts))
        sentiments: List[int] = []
        for doc in docs:
            annotation = self._retrieve_sentiment(doc)
            sentiments.append(annotation)
        return sentiments

    def _retrieve_sentiment(self, doc: spacy.language.Doc) -> int:
        words = []
        for lemma, pos in [(token.lemma_, token.pos_) for token in doc]:
            words.append(models.Word(lemma=lemma, pos=pos))
        annotations = self._repo.get_annotations(words=words)
        return self._get_weighted_sentiment(annotations)

    @staticmethod
    def _get_weighted_sentiment(annotations: List[models.SentimentAnnotation]):
        weights = {
            'ADJ': 2,
            'VERB': 4,
        }

        defined = [annotation for annotation in annotations if annotation.annotation != 0]
        calc = {'annotations': 0, 'weights': 0}
        for annotation in defined:
            weight = weights[annotation.word.pos] if annotation.word.pos in weights else 1
            calc['annotations'] += annotation.annotation * weight
            calc['weights'] += weight
        return round(calc['annotations'] / calc['weights'])
