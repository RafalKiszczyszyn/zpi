from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Union
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
        tokens = [(token.lemma_, token.pos_) for token in doc]

        print(tokens)

        phrases: List[models.Sample] = []
        word: Union[models.Word, None] = None
        for index, token in enumerate(tokens):
            lemma, pos = token
            if word is not None:
                phrases.append(models.Phrase(text=f'{word.text} {lemma}', words=2, index=index-1, pos='X'))
            word = models.Word(text=lemma, pos=pos, index=index)

        phrase_annotations = self._repo.get_annotations(samples=phrases, defined_only=True)
        used_indices = set()
        for annotation in phrase_annotations:
            used_indices.add(annotation.sample.index)
            used_indices.add(annotation.sample.index + 1)

        words: List[models.Word] = []
        for index, token in enumerate(tokens):
            if index in used_indices:
                continue

            lemma, pos = token
            words.append(models.Word(text=lemma, pos=pos, index=index))

        word_annotations = self._repo.get_annotations(samples=words, defined_only=True)
        return self._get_weighted_sentiment(phrase_annotations + word_annotations)

    @staticmethod
    def _get_weighted_sentiment(annotations: List[models.SentimentAnnotation]):
        weights = {
            'ADJ': 2,
            'VERB': 4,
        }

        defined = [annotation for annotation in annotations if annotation.annotation != 0]
        if len(defined) == 0:
            return 0

        calc = {'annotations': 0, 'weights': 0}
        for annotation in defined:
            weight = weights[annotation.sample.pos] if annotation.sample.pos in weights else 1
            calc['annotations'] += annotation.annotation * weight
            calc['weights'] += weight
        return round(calc['annotations'] / calc['weights'])
