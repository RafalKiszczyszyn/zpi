import uuid
from abc import abstractmethod, ABC


class IGuidGenerator(ABC):

    @abstractmethod
    def generate(self) -> str:
        pass


class GuidGenerator(IGuidGenerator):

    def __init__(self, prefix=None, postfix=None):
        self._prefix = prefix if prefix else ''
        self._postfix = postfix if postfix else ''

    def generate(self):
        return self._prefix + str(uuid.uuid4()) + self._postfix
