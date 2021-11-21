from datetime import datetime
from traceback import TracebackException
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


class StdoutLogger(ILogger):

    def info(self, info: str):
        self.print(tag='[INFO]', message=info)

    def warning(self, warning: str):
        self.print(tag='[WARNING]', message=warning)

    def error(self, message, error: Exception):
        traceback = "".join(TracebackException.from_exception(error).format())
        self.print(tag='[ERROR]', message=f'{message}:\n{traceback}')

    @staticmethod
    def print(tag, message):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        tag = tag.rjust(10, " ")
        print(f'{timestamp} {tag} {message}')
