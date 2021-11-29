from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Iterable, List


@dataclass(frozen=True)
class Event:
    topic: str
    tag: int
    body: str = field(repr=False)


@dataclass(frozen=True)
class Message:
    body: str = field(repr=False)
    persistence: bool = False
    mandatory: bool = False


@dataclass
class Result:
    event: Event


@dataclass
class Accept(Result):
    message: Union[str, None] = None


@dataclass
class Reject(Result):
    requeue: bool = False
    error: Union[Exception, None] = None


class ChannelMode(Enum):
    PUBLISHING = 1
    CONSUMING = 2
    BIDIRECTIONAL = 3


class IChannel(ABC):

    @property
    @abstractmethod
    def mode(self) -> ChannelMode:
        pass

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        pass

    @abstractmethod
    def publish(self, message: Message):
        pass

    @abstractmethod
    def consume(self) -> Iterable[Event]:
        pass

    @abstractmethod
    def cancel(self):
        pass

    @abstractmethod
    def accept(self, event: Event):
        pass

    @abstractmethod
    def reject(self, event: Event, requeue: bool = False):
        pass

    @abstractmethod
    def close(self):
        pass


class IConnection(ABC):

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        pass

    @abstractmethod
    def keep_alive(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def publisher(self, topic: str) -> IChannel:
        pass

    @abstractmethod
    def consumer(self, topics: List[str]) -> IChannel:
        pass


class IConnectionFactory(ABC):

    @abstractmethod
    def create(self) -> IConnection:
        pass


class IEventHandler(ABC):

    @abstractmethod
    def handle(self, event: Event) -> Result:
        pass
