import os
import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))
import shutil

from feedreader.apirest import management


from unittest import TestCase, mock


def raiseException():
    raise Exception()


class TasksTests(TestCase):

    SOURCES = str(pathlib.Path('./temp/sources.json').resolve())

    @classmethod
    def setUpClass(cls) -> None:
        os.mkdir('./temp')

    def test_GET_SourcesAreReturned(self):
        # Arrange
        content = '[{"key": "value"}]'
        with open(self.SOURCES, 'w') as file:
            file.write(content)
        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.get()

        # Assert
        self.assertEqual(body, [{"key": "value"}])
        self.assertEqual(status, 200)

    @mock.patch('feedreader.apirest.management.Request')
    def test_POST_InvalidRequest(self, requestMock):
        # Arrange
        requestMock().getJson.return_value = {}
        open(self.SOURCES, 'w').close()
        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.post()

        # Assert
        self.assertTrue("message" in body)
        self.assertTrue(status, 400)

    @mock.patch('feedreader.apirest.management.Request')
    def test_POST_PostedTaskIsInvalid(self, requestMock):
        # Arrange
        requestMock().getJson.return_value = {
            "name": "TaskName", "steps": [{"name": "StepName", "implementation": "module.ClassName"}]}
        open(self.SOURCES, 'w').close()
        builderMock = mock.MagicMock()
        builderMock.build = raiseException
        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=builderMock)

        # Act
        body, status = sut.post()

        # Assert
        self.assertTrue("message" in body)
        self.assertTrue(body["message"].find("built") != -1)
        self.assertTrue(status, 400)

    @mock.patch('feedreader.apirest.management.Request')
    def test_POST_ValidRequest(self, requestMock):
        # Arrange
        requestMock().getJson.return_value = {
            "name": "TaskName", "steps": [{"name": "StepName", "implementation": "module.ClassName"}]}
        open(self.SOURCES, 'w').close()
        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.post()

        # Assert
        self.assertIsNone(body)
        self.assertTrue(status, 201)
        with open(self.SOURCES, 'r') as f:
            content = f.read()
            self.assertTrue(content.find("TaskName") != -1)
            self.assertTrue(content.find("module.ClassName") != -1)

    def test_DELETE_TaskNameIsUndefined(self):
        # Arrange
        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.delete()

        # Assert
        self.assertIsNone(body)
        self.assertTrue(status, 400)

    def test_DELETE_TaskNameDoesNotExist(self):
        # Arrange
        with open(self.SOURCES, 'w') as f:
            f.write("{}")

        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.delete(taskName='TaskName')

        # Assert
        self.assertIsNone(body)
        self.assertTrue(status, 400)

    def test_DELETE_TaskNameExist(self):
        # Arrange
        with open(self.SOURCES, 'w') as f:
            f.write('[{"name": "TaskName"}]')

        sut = management.Tasks(appSettings=self.SOURCES, taskBuilder=mock.MagicMock())

        # Act
        body, status = sut.delete(taskName='TaskName')

        # Assert
        self.assertEqual(body, 1)
        self.assertTrue(status, 200)
        with open(self.SOURCES, 'r') as f:
            self.assertEqual(f.read(), "[]")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree('./temp', ignore_errors=True)
