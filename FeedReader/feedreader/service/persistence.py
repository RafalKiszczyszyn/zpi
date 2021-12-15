from abc import abstractmethod, ABC
from typing import List

from pymongo import mongo_client
from pymongo.collection import Collection

from feedreader.service import models


class IArticlesDataAccess(ABC):

    @abstractmethod
    def insert(self, articles: List[models.Article]):
        pass

    @abstractmethod
    def find_existing_ids(self, indices: List[str]) -> List[str]:
        pass


class ArticlesDataAccess(IArticlesDataAccess):

    def __init__(self, url, db_name, collection_name, ttl):
        self._url = url
        self._db_name = db_name
        self._collection_name = collection_name
        self._ttl = ttl

    def insert(self, articles: List[models.Article]):
        if len(articles) == 0:
            return

        client, collection = self._connect()
        docs = map(self._map_to_doc, articles)
        collection.insert_many(list(docs))
        client.close()

    def find_existing_ids(self, indices: List[str]) -> List[str]:
        client, collection = self._connect()
        docs = collection.find({"_id": {"$in": indices}})
        client.close()
        return list(map(lambda doc: doc["_id"], docs))

    def _connect(self) -> (mongo_client.MongoClient, Collection):
        client = mongo_client.MongoClient(self._url)
        db = client[self._db_name]
        collection = db[self._collection_name]
        collection.create_index("published", name="published_index", expireAfterSeconds=self._ttl)

        return client, collection

    @staticmethod
    def _map_to_doc(article: models.Article) -> dict:
        return {
            '_id': article.guid,
            'published': article.published
        }


class IArticlesRepository(ABC):

    @abstractmethod
    def filter_existing(self, ids: List[str]) -> List[str]:
        pass

    @abstractmethod
    def save(self, articles: List[models.Article]):
        pass


class ArticlesRepository(IArticlesRepository):

    def __init__(self, data_access: IArticlesDataAccess):
        self._data_access = data_access

    def filter_existing(self, ids: List[str]) -> List[str]:
        stored_ids = set(self._data_access.find_existing_ids(ids))
        return list(set(ids) - stored_ids)

    def save(self, articles: List[models.Article]):
        self._data_access.insert(articles)
