from abc import ABC, abstractmethod

from broker import logging


class EndpointBase(ABC):
    pass


class SourceEndpointBase(EndpointBase):

    @abstractmethod
    def pull(self):
        pass


class DestinationEndpointBase(EndpointBase):

    @abstractmethod
    def push(self, content):
        pass


# Endpoints' implementations


class HttpEndpointBase(ABC):

    def __init__(self, *args, **kwargs):
        self.__initialise(**kwargs)

    def __initialise(self, **kwargs):
        self.__url = kwargs['url']
        self.__method = kwargs['method']
        self.__params = kwargs['params']


class HttpSourceEndpoint(HttpEndpointBase, SourceEndpointBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pull(self, **kwargs):
        if logging.logger:
            logging.logger.log("Pulling")
        return 'CONTENT'


class HttpDestinationEndpoint(HttpEndpointBase, DestinationEndpointBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def push(self, content, **kwargs):
        if logging.logger:
            logging.logger.log("Pushing")
        print(content)
