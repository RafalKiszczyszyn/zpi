from abc import ABC, abstractmethod


class ILogger(ABC):

    @abstractmethod
    def info(self, info: str):
        pass

    @abstractmethod
    def warning(self, warning: str):
        pass

    @abstractmethod
    def error(self, message, error: Exception):
        pass
