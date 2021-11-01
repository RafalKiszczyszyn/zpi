from abc import abstractmethod, ABC
from datetime import datetime


class LoggerBase(ABC):
    @abstractmethod
    def log(self, content):
        pass


# Logger's implementations


class FileLogger(LoggerBase):

    def __init__(self, filename):
        self.filename = filename

    def log(self, content):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        log = f"[{timestamp}] {content}\n"
        with open(self.filename, 'a') as logs_file:
            print(log, end='')
            logs_file.write(log)


class DebugLogger(LoggerBase):

    def log(self, content):
        print(content)
