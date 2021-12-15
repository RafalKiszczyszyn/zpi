import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from datetime import datetime
from unittest import TestCase, mock

from feedreader.service import models


class DataAccessTests(TestCase):

    Url = "Url"
    DbName = "DbName"
    CollectionName = "CollectionName"
    Ttl = 60

    class MongoDbMock:

        def __init__(self):
            self.collection = mock.MagicMock()

        def __getitem__(self, item):
            if item == DataAccessTests.CollectionName:
                return self.collection

    class MongoClientMock:

        def __init__(self, *args):
            self.db = DataAccessTests.MongoDbMock()
            self.close = mock.MagicMock()

        def __getitem__(self, item):
            if item == DataAccessTests.DbName:
                return self.db

    @mock.patch('pymongo.mongo_client.MongoClient')
    def test_Insert_NoArticles_NoConnectionIsMade(self, mongoClientMock):
        from feedreader.service.persistence import ArticlesDataAccess

        # Arrange
        sut = ArticlesDataAccess(
            url=self.Url, db_name=self.DbName, collection_name=self.CollectionName, ttl=self.Ttl)

        # Act
        sut.insert([])

        # Assert
        mongoClientMock().assert_not_called()

    @mock.patch('pymongo.mongo_client.MongoClient')
    def test_Insert_ManyArticles_ManyDocsInserted(self, mongoClientMock):
        from feedreader.service.persistence import ArticlesDataAccess
        mongoClientMock.return_value = self.MongoClientMock()

        # Arrange
        sut = ArticlesDataAccess(
            url=self.Url, db_name=self.DbName, collection_name=self.CollectionName, ttl=self.Ttl)
        articles = [
            models.Article(
                guid="ABC1",
                title="Title1",
                summary="Summary1",
                published=datetime.now(),
                updated=datetime.now(),
                link="https://example.com",
                enclosures=[]),
            models.Article(
                guid="ABC2",
                title="Title2",
                summary="Summary2",
                published=datetime(2020, 10, 10),
                updated=datetime.now(),
                link="https://example.com",
                enclosures=[])
        ]

        # Act
        sut.insert(articles)

        # Assert
        mongoClientMock().db.collection.create_index.assert_called_once_with(
            "published", name="published_index", expireAfterSeconds=self.Ttl)
        mongoClientMock().db.collection.insert_many.assert_called_once_with(list(map(lambda article: {
            '_id': article.guid,
            'published': article.published
        }, articles)))
        mongoClientMock().close.assert_called_once()

    @mock.patch('pymongo.mongo_client.MongoClient')
    def test_Find_ManyIndices(self, mongoClientMock):
        from feedreader.service.persistence import ArticlesDataAccess
        mongoClientMock.return_value = self.MongoClientMock()

        # Arrange
        sut = ArticlesDataAccess(
            url=self.Url, db_name=self.DbName, collection_name=self.CollectionName, ttl=self.Ttl)
        indices = ["abc", "xyz"]

        # Act
        sut.find_existing_ids(indices)

        # Assert
        mongoClientMock().db.collection.create_index.assert_called_once_with(
            "published", name="published_index", expireAfterSeconds=self.Ttl)
        mongoClientMock().db.collection.find.assert_called_once_with({"_id": {"$in": indices}})
        mongoClientMock().close.assert_called_once()


class RepositoryTests(TestCase):

    def test_FilterExisting_NonexistentIdsAreReturned(self):
        from feedreader.service.persistence import ArticlesRepository

        # Arrange
        daMock = mock.MagicMock()
        daMock.find_existing_ids.return_value = ["ABC", "XYZ"]
        sut = ArticlesRepository(data_access=daMock)

        # Act
        nonexistentIds = sut.filter_existing(["ABC", "DEF"])

        # Assert
        self.assertSequenceEqual(nonexistentIds, ["DEF"])
