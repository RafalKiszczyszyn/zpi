from abc import ABC, abstractmethod

from wordnet import events


class IQueueController(ABC):

    @abstractmethod
    def consume(self, message: str) -> events.Response:
        pass


class TestQueueController(IQueueController):

    def consume(self, message: str) -> events.Response:
        print(TestQueueController.__name__, 'received message', message)
        return events.Ack('Done!')
