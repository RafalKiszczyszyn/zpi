from abc import ABC, abstractmethod

from broker import logging


class EndpointBase(ABC):

    def __init__(self, **kwargs):
        if 'task_name' in kwargs:
            self.task_name = kwargs['task_name']
        else:
            self.task_name = None


class SourceEndpointBase(EndpointBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def pull(self):
        pass


class DestinationEndpointBase(EndpointBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def push(self, content):
        pass


# Endpoints' implementations


class HttpEndpointBase(ABC):

    def _initialise(self, **kwargs):
        self.__url = kwargs['url']
        self.__method = kwargs['method']
        self.__params = kwargs['params']


class HttpSourceEndpoint(SourceEndpointBase, HttpEndpointBase):

    def __init__(self, **kwargs):
        super(SourceEndpointBase, self).__init__(**kwargs)
        self._initialise(**kwargs)

    def pull(self, **kwargs):
        if logging.logger:
            logging.logger.log(f"{self.task_name} - Pulling")
        return 'CONTENT'


class HttpDestinationEndpoint(DestinationEndpointBase, HttpEndpointBase):

    def __init__(self, **kwargs):
        super(DestinationEndpointBase, self).__init__(**kwargs)
        self._initialise(**kwargs)

    def push(self, content, **kwargs):
        if logging.logger:
            logging.logger.log(f"{self.task_name} - Pushing")
        print(content)
