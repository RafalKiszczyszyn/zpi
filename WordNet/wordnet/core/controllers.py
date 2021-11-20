from abc import ABC, abstractmethod
from wordnet.core import events


class IQueueController(ABC):

    @abstractmethod
    def consume(self, message: str) -> events.Response:
        pass
