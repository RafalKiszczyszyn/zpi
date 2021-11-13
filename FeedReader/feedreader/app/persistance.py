from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import List

from pymongo import MongoClient
from pymongo.collection import Collection


@dataclass
class ArticleDao:
    id: str
    published: datetime


class IArticlesDataAccess(ABC):

    @abstractmethod
    def insert(self, articles: List[ArticleDao]):
        pass

    @abstractmethod
    def get_by_ids(self, indices: List[str]) -> List[ArticleDao]:
        pass


class ArticlesDataAccess(IArticlesDataAccess):

    def __init__(self, url, db_name, collection_name, ttl):
        self._url = url
        self._db_name = db_name
        self._collection_name = collection_name
        self._ttl = ttl

    def insert(self, articles: List[ArticleDao]):
        if len(articles) == 0:
            return

        client, collection = self._connect()
        docs = map(self._map_to_doc, articles)
        collection.insert_many(docs)
        client.close()

    def get_by_ids(self, indices: List[str]) -> List[ArticleDao]:
        client, collection = self._connect()
        docs = collection.find({"_id": {"$in": indices}})
        client.close()
        return list(map(self._map_to_article, docs))

    def _connect(self) -> (MongoClient, Collection):
        client = MongoClient(self._url)
        db = client[self._db_name]
        collection = db[self._collection_name]
        collection.create_index("published", name="published_index", expireAfterSeconds=self._ttl)

        return client, collection

    @staticmethod
    def _map_to_doc(article: ArticleDao) -> dict:
        return {
            '_id': article.id,
            'published': article.published
        }

    @staticmethod
    def _map_to_article(doc: dict):
        return ArticleDao(id=doc['_id'], published=doc['published'])


class IArticlesRepository(ABC):

    @abstractmethod
    def filter_existing(self, ids: List[str]) -> List[str]:
        pass

    @abstractmethod
    def save(self, articles: List[ArticleDao]):
        pass


class ArticlesRepository(IArticlesRepository):

    def __init__(self, data_access: IArticlesDataAccess):
        self._data_access = data_access

    def filter_existing(self, ids: List[str]) -> List[str]:
        stored_articles = self._data_access.get_by_ids(ids)
        stored_ids = set([article.id for article in stored_articles])
        return list(set(ids) - stored_ids)

    def save(self, articles: List[ArticleDao]):
        self._data_access.insert(articles)
