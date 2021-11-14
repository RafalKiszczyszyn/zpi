from abc import ABC, abstractmethod

from wordnet import events, nlp


class IQueueController(ABC):

    @abstractmethod
    def consume(self, message: str) -> events.Response:
        pass


class TestQueueController(IQueueController):

    def consume(self, message: str) -> events.Response:
        print(f"Message={message}")
        sentiments = nlp.get_pipeline().retrieve_sentiments(message)
        print(f"Sentiments={sentiments}")
        return events.Ack('Done!')
