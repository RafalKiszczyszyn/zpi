from abc import ABC, abstractmethod
from typing import List, Union, Set
import os
import zipfile
import pathlib
from uuid import uuid4


class IWorkspaceManager(ABC):

    @property
    @abstractmethod
    def working_dir(self):
        pass

    @abstractmethod
    def save_many(self, contents: List[Union[str, bytes]]) -> List[str]:
        pass

    @abstractmethod
    def save(self, content: Union[str, bytes], ext: Union[str, None] = None):
        pass

    @abstractmethod
    def compress(self, files: List[str]) -> str:
        pass

    @abstractmethod
    def decompress(self, archive) -> List[str]:
        pass

    @abstractmethod
    def clear(self):
        pass
    

class WorkspaceManager(IWorkspaceManager):

    def __init__(self, wd: str):
        self._wd: str = str(pathlib.Path(wd).resolve())
        self._resources: Set[str] = set()

    @property
    def working_dir(self):
        return self._wd

    def save_many(self, contents: List[Union[str, bytes]]) -> List[str]:
        filenames: List[str] = []
        for content in contents:
            filenames.append(self.save(content))
        return filenames

    def save(self, content: Union[str, bytes], ext: Union[str, None] = None):
        mode = "w" if isinstance(content, str) else 'wb'
        ext = ext if ext else '.txt' if mode == 'w' else '.bin'
        
        guid = uuid4()
        filename = os.path.join(self.working_dir, str(guid)) + ext
        self._resources.add(filename)
        with open(filename, mode) as file:
            file.write(content)
        return filename

    def decompress(self, archive) -> List[str]:
        with zipfile.ZipFile(archive, 'r') as archive:
            archive.extractall(self.working_dir)
            filenames = [os.path.join(self.working_dir, info.filename) for info in archive.infolist()]
        self._resources |= set(filenames)
        return filenames

    def compress(self, files: List[str]) -> str:
        path = os.path.join(self.working_dir, str(uuid4())) + '.zip'
        self._resources.add(path)
        with zipfile.ZipFile(path, 'w') as archive:
            for file in files:
                archive.write(file, arcname=os.path.basename(file))
        return path

    def clear(self):
        for resource in self._resources:
            if os.path.exists(resource):
                os.remove(resource)
