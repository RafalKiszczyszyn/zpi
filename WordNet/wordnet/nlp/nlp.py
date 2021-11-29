from abc import ABC, abstractmethod
import json
from typing import Dict, List
import requests
import time
import pandas

from . import persistence


class INlpService(ABC):

    @abstractmethod
    def polarity(self, texts: List[str]) -> List[float]:
        pass


class ClarinNlpService(INlpService):

    def __init__(self, user: str, manager: persistence.IWorkspaceManager) -> None:
        self._manager = manager
        self._user = user
        self._task = 'any2txt|wcrft2({"morfeusz2":true})|wsd|sentiment|out("senti")|' \
                     'sentimerge({"split_paragraphs":"False"})'
        self._url = "http://ws.clarin-pl.eu/nlprest2/base"

    def polarity(self, texts: List[str]) -> List[float]:
        polarities: List[float] = [0.0 for _ in range(len(texts))]
        _map: Dict[str, int] = {}
        try:
            filenames = self._manager.save_many(texts)
            _map = {filename: index for index, filename in enumerate(filenames)}
            archive = self._manager.compress(filenames)
            _bytes = self._process(archive)
            archive = self._manager.save(_bytes, ext='.zip')
            filenames = self._manager.decompress(archive)
            for filename in filenames:
                df = pandas.read_csv(filename, sep=';')
                count = len(df[df['Polarity'] != 0])
                count = count if count else 1
                polarity = df['Polarity'].sum() / count 
                polarities[_map[filename]] = polarity
        finally:
            self._manager.clear()
        return polarities

    def _process(self, archive: str):
        file_id = self._upload(archive)
        params = {"user": self._user, "lpmn": f"filezip({file_id})|{self._task}|dir|makezip"}

        task_id = requests.post(self._url + '/startTask/', data=json.dumps(params)).text
        time.sleep(0.2)
        response = self._await_task(task_id=task_id)
        
        if response["status"] == 'ERROR':
            return None

        return self._download(file_id=response['value']['result'][0]['fileID'])

    def _await_task(self, task_id: str) -> Dict:
        response = requests.get(self._url+'/getStatus/' + task_id)
        response = response.json()
        while response["status"] in ["QUEUE", "PROCESSING"]:
            time.sleep(0.5)
            response = requests.get(self._url+'/getStatus/' + task_id).json()
        return response

    def _upload(self, archive) -> str:
        with open(archive, "rb") as _bytes:
            content = _bytes.read()
        return requests.post(
            url=self._url+'/upload/', 
            data=content, 
            headers={'Content-Type': 'binary/octet-stream'}).text

    def _download(self, file_id: str) -> bytes:
        return requests.get(self._url+'/download' + file_id).content
