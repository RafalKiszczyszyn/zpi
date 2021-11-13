from abc import abstractmethod, ABC
from datetime import datetime
from traceback import TracebackException


class LoggerBase(ABC):
    @abstractmethod
    def log(self, content: str):
        pass

    @abstractmethod
    def log_error(self, info: str, e: BaseException):
        pass


# Logger's implementations


class StdoutLogger(LoggerBase):

    def log(self, content: str):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        log = f"[{timestamp}] {content}\n"
        print(log, end='')

    def log_error(self, info: str, e: BaseException):
        traceback = "".join(TracebackException.from_exception(e).format())
        self.log(content=f"{info}\n{traceback}")
