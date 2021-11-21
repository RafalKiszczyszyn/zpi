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
    def get_annotations(self, sample: models.Sample) -> List[models.SentimentAnnotation]:
        pass


class ISentimentAnnotationsDataAccessFactory(ABC):

    @abstractmethod
    def create(self) -> ISentimentAnnotationsDataAccess:
        pass


class ISentimentAnnotationsRepository(ABC):

    @abstractmethod
    def get_annotations(self, samples: List[models.Sample], defined_only=False) -> List[models.SentimentAnnotation]:
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

    def get_annotations(self, sample: models.Sample) -> List[models.SentimentAnnotation]:
        if isinstance(sample, models.Word):
            where = 'WHERE lemma=:lemma AND pos=:pos'
            params = {'lemma': sample.text, 'pos': sample.pos}
        else:
            where = 'WHERE lemma=:lemma'
            params = {'lemma': sample.text}

        cursor = self._conn.execute(
            f'''
            SELECT annotation 
            FROM Annotations
            {where}''', params)

        annotations = []
        for row in cursor:
            annotation = models.SentimentAnnotation(
                sample=sample, annotation=row[0])
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

    def get_annotations(self, samples: List[models.Sample], defined_only=False) -> List[models.SentimentAnnotation]:
        with self._data_access_factory.create() as data_access:
            annotations = []
            for sample in samples:
                annotations_ = data_access.get_annotations(sample)
                if len(annotations_) != 0:
                    annotations.append(annotations_[0])
                elif not defined_only:
                    annotations.append(
                        models.SentimentAnnotation(sample=sample, annotation=0)
                    )
            return annotations
