import os
from abc import abstractmethod, ABC
from datetime import datetime
from os.path import isfile, exists, dirname

from broker import core


class LoggerBase(ABC):
    @abstractmethod
    def log(self, content):
        pass


# Logger's implementations


class FileLogger(LoggerBase):

    class Meta:
        args = core.ConfigArgs(required=['filename'], validate=True)

    def __init__(self, *args, **kwargs):
        self.filename = None

    def validate_config_args(self):
        if exists(self.filename):
            if isfile(self.filename) and os.access(self.filename, os.W_OK):
                return
            raise Exception(f'No permissions to write to file {self.filename}. '
                            f'Consider running broker as a different user.')

        parent_dir = dirname(self.filename)
        if not parent_dir:
            parent_dir = '.'

        if not os.access(parent_dir, os.W_OK):
            raise Exception(f'No permissions to write to folder {self.filename}.'
                            f'Consider running broker as a different user.')
        pass

    def log(self, content):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        log = f"[{timestamp}] {content}\n"
        with open(self.filename, 'a') as logs_file:
            print(log, end='')
            logs_file.write(log)
