from abc import ABC, abstractmethod
import sqlite3
from typing import List

from . import models


""" ----- TYPES ---- """


class ISentimentAnnotationsDataAccess(ABC):

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_annotations(self, word: models.Word) -> List[models.SentimentAnnotation]:
        pass


class ISentimentAnnotationsDataAccessFactory(ABC):

    @abstractmethod
    def create(self) -> ISentimentAnnotationsDataAccess:
        pass


class ISentimentAnnotationsRepository(ABC):

    @abstractmethod
    def get_annotations(self, words: List[models.Word]) -> List[models.SentimentAnnotation]:
        pass


""" ----- IMPLEMENTATIONS ----- """


class PlWordNetDataAccess(ISentimentAnnotationsDataAccess):

    # noinspection PyTypeChecker
    def __init__(self, connection_string):
        self._conn = sqlite3.Connection(connection_string)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._conn.close()

    def get_annotations(self, word: models.Word) -> List[models.SentimentAnnotation]:
        cursor = self._conn.execute(
            '''
            SELECT lemma, pos, annotation 
            FROM Annotations
            WHERE lemma=:lemma AND pos=:pos
            ''', {'lemma': word.lemma, 'pos': word.pos})

        annotations = []
        for row in cursor:
            annotation = models.SentimentAnnotation(
                word=models.Word(lemma=row[0], pos=row[1]), annotation=row[2])
            annotations.append(annotation)

        return annotations


class PlWordNetDataAccessFactory(ISentimentAnnotationsDataAccessFactory):

    def __init__(self, connection_string):
        self._connection_string = connection_string

    def create(self) -> ISentimentAnnotationsDataAccess:
        return PlWordNetDataAccess(connection_string=self._connection_string)


class SentimentAnnotationsRepository(ISentimentAnnotationsRepository):

    def __init__(self, data_access_factory: ISentimentAnnotationsDataAccessFactory):
        self._data_access_factory = data_access_factory

    def get_annotations(self, words: List[models.Word]) -> List[models.SentimentAnnotation]:
        with self._data_access_factory.create() as data_access:
            annotations = []
            for word in words:
                _annotations = data_access.get_annotations(word)
                annotation: models.SentimentAnnotation
                if len(_annotations) == 0:
                    annotation = models.SentimentAnnotation(word=word, annotation=0)
                else:
                    annotation = _annotations[0]
                annotations.append(annotation)
            return annotations
