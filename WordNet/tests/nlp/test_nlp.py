import pathlib
import sys; sys.path.append(pathlib.Path(__file__).parent.parent.parent.resolve())

from contextlib import contextmanager
from unittest import TestCase, mock

import pandas

from wordnet.nlp import nlp, persistence


class AverageTests(TestCase):

    def test_Calc_DataFrameWithNonNumericValuesAndZeros_ZerosNonNumericValuesAreIgnored(self):
        # Arrange
        df = pandas.DataFrame(["Text", 1, "Text", 0, -1, -1], columns=["Polarity"])

        # Act
        average = nlp.Average().calc(df)

        # Assert
        self.assertEqual(average, sum([1, -1, -1]) / 3)

    def test_Calc_DataFrameWithZerosOnly_ZerosNonNumericValuesAreIgnored(self):
        # Arrange
        df = pandas.DataFrame(["Text", 0, "Text", 0, 0, 0], columns=["Polarity"])

        # Act
        average = nlp.Average().calc(df)

        # Assert
        self.assertEqual(average, 0.0)


class ClarinNlpServiceTests(TestCase):

    class ClarinApiMock:

        def __init__(self, responses):
            self.responses = {method: iter(responses[method]) for method in responses}
            self.uploaded = None

        @contextmanager
        def patch(self):
            with mock.patch("requests.get", side_effect=self.request):
                with mock.patch("requests.post", side_effect=self.request):
                    yield

        def request(self, **kwargs):
            if kwargs['url'].find('upload') != -1:
                return self.upload(kwargs['data'])

            if kwargs['url'].find('startTask') != -1:
                return self.startTask()

            if kwargs['url'].find('getStatus') != -1:
                return self.getStatus()

            if kwargs['url'].find('download') != -1:
                return self.download()

            return mock.MagicMock()

        def upload(self, body):
            self.uploaded = body
            response = mock.MagicMock()
            if "upload" in self.responses:
                response.text = next(self.responses["upload"])
            return response

        def startTask(self):
            response = mock.MagicMock()
            if "startTask" in self.responses:
                response.text = next(self.responses["startTask"])
            return response

        def getStatus(self):
            response = mock.MagicMock()
            if "getStatus" in self.responses:
                response.json = lambda: next(self.responses["getStatus"])
            return response

        def download(self):
            response = mock.MagicMock()
            response.content = self.uploaded
            return response

    def test_Polarity_ClarinApiError_ExceptionIsRaised(self):
        # Arrange
        apiMock = self.ClarinApiMock(responses={
            "getStatus": [{"status": "ERROR", "value": "Something went wrong!"}],
            "upload": ["fileID"],
            "startTask": ["taskID"]
        })
        sut = nlp.ClarinNlpService(
            user="test",
            algorithm=mock.MagicMock(),
            manager=persistence.WorkspaceManager(wd="."))

        with apiMock.patch():
            # Act + Assert
            self.assertRaises(Exception, sut.polarity, ["Alice has a cat"])

    @mock.patch('pandas.read_csv')
    def test_Polarity_RequestIsSuccessful_PolarityIsReturned(self, _):
        # Arrange
        apiMock = self.ClarinApiMock(responses={
            "getStatus": [
                {"status": "QUEUE"},
                {"status": "PROCESSING"},
                {"status": "DONE", "value": {"result": [{"fileID": "fileID"}]}}
            ],
            "upload": ["fileID"],
            "startTask": ["taskID"]
        })

        algorithmMock = mock.MagicMock()
        algorithmMock.calc.return_value = -0.9

        sut = nlp.ClarinNlpService(
            user="test",
            algorithm=algorithmMock,
            manager=persistence.WorkspaceManager(wd="."))

        with apiMock.patch():
            # Act
            polarities = sut.polarity(["Alice has a cat"])

        # Assert
        self.assertSequenceEqual(polarities, [-0.9])
