from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IQueue(ABC):
    name: str


class Response(ABC):
    pass


@dataclass(frozen=True)
class Ack(Response):
    message: str


@dataclass(frozen=True)
class Nack(Response):
    requeue: bool


class IQueueConsumer(ABC):

    @abstractmethod
    def consume(self):
        pass

    @abstractmethod
    def stop(self):
        pass
