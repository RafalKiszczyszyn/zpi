from traceback import TracebackException

from feedreader.service.loggers import LoggerBase


class DebugLogger(LoggerBase):

    def log(self, content):
        print(content)

    def log_error(self, info, e: BaseException):
        traceback = "".join(TracebackException.from_exception(e).format())
        log = f"{info}\n{traceback}\n"
        print(log)
