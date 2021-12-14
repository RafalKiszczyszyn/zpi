from abc import ABC, abstractmethod
import json
from typing import Dict, List, Tuple
import requests
import time
import pandas

from wordnet.nlp import persistence


class INlpService(ABC):

    @abstractmethod
    def polarity(self, texts: List[str]) -> List[float]:
        pass


class IStatisticAnalysisAlgorithm(ABC):

    @abstractmethod
    def calc(self, dataFrame: pandas.DataFrame) -> float:
        pass


class Average(IStatisticAnalysisAlgorithm):

    def calc(self, df: pandas.DataFrame) -> float:
        polarity = pandas.to_numeric(df['Polarity'], errors="coerce").fillna(0)
        polarity = polarity[polarity != 0]
        count = polarity.count() if polarity.count() else 1
        return polarity.sum() / count


class ClarinNlpService(INlpService):

    def __init__(self,
                 user: str,
                 algorithm: IStatisticAnalysisAlgorithm,
                 manager: persistence.IWorkspaceManager) -> None:
        self._algorithm = algorithm
        self._manager = manager
        self._user = user
        self._task = 'any2txt|wcrft2|wsd|ccl_emo({"lang":"polish"})|out("ccl_emo")' \
                     '|ccl_emo_stats({"lang":"polish", "split_paragraphs": false})'
        self._url = "http://ws.clarin-pl.eu/nlprest2/base"

    def polarity(self, texts: List[str]) -> List[float]:
        polarities: List[float] = [0.0 for _ in range(len(texts))]
        try:
            csv, _map = self._process(texts)
            for name in csv:
                df = pandas.read_csv(name, sep=';')
                polarities[_map[name]] = self._algorithm.calc(df)
        finally:
            self._manager.clear()
        return polarities

    def _process(self, texts: List[str]) -> Tuple[List[str], Dict[str, int]]:
        fileNames = self._manager.save_many(texts)
        _map = {filename: index for index, filename in enumerate(fileNames)}

        archive = self._manager.compress(fileNames)
        _bytes = self._request(archive)
        archive = self._manager.save(_bytes, ext='.zip')

        return self._manager.decompress(archive), _map

    def _request(self, archive: str):
        file_id = self._upload(archive)
        params = {"user": self._user, "lpmn": f"filezip({file_id})|{self._task}|dir|makezip"}

        task_id = requests.post(url=self._url + '/startTask/', data=json.dumps(params)).text
        time.sleep(0.2)
        response = self._await_task(task_id=task_id)

        if response["status"] == 'ERROR':
            raise Exception(f"Clarin nlprest2 error: {response['value']}")

        return self._download(file_id=response['value']['result'][0]['fileID'])

    def _await_task(self, task_id: str) -> Dict:
        response = requests.get(url=self._url+'/getStatus/' + task_id)
        response = response.json()
        while response["status"] in ["QUEUE", "PROCESSING"]:
            time.sleep(0.5)
            response = requests.get(url=self._url+'/getStatus/' + task_id).json()
        return response

    def _upload(self, archive) -> str:
        with open(archive, "rb") as _bytes:
            content = _bytes.read()
        return requests.post(
            url=self._url+'/upload/',
            data=content,
            headers={'Content-Type': 'binary/octet-stream'}).text

    def _download(self, file_id: str) -> bytes:
        return requests.get(url=self._url+'/download' + file_id).content
