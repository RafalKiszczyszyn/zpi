from abc import abstractmethod, ABC
from datetime import datetime


class LoggerBase(ABC):
    @abstractmethod
    def log(self, content):
        pass


logger: LoggerBase = None


def log_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if logger:
                logger.log(f"Exception: {e}")
    return wrapper


# Logger's implementations


class FileLogger(LoggerBase):

    def log(self, content):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        log = f"[{timestamp}] {content}\n"
        with open('logs', 'a') as logs_file:
            logs_file.write(log)
