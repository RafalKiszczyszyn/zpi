from abc import ABC, abstractmethod
from broker import loggers as logs
import requests


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
        # Load required fields
        self._method = kwargs['method']
        self._url = kwargs['url']

        # Load optional fields
        if 'params' in kwargs:
            self._params = kwargs['params']
        if 'body' in kwargs:
            self._body = kwargs['body']
        if 'headers' in kwargs:
            self._headers = kwargs['headers']

    def get_request_kwargs(self):
        kwargs = {}
        if hasattr(self, '_params'):
            kwargs['params'] = self._params
        if hasattr(self, '_body'):
            kwargs['body'] = self._body
        if hasattr(self, '_headers'):
            kwargs['headers'] = self._headers
        return kwargs

    @classmethod
    def _log(cls, message):
        if logs.logger:
            logs.logger.log(message)


class HttpSourceEndpoint(SourceEndpointBase, HttpEndpointBase):

    def __init__(self, *args, **kwargs):
        super(SourceEndpointBase, self).__init__(**kwargs)
        self._initialise(**kwargs)

    def pull(self, **kwargs):
        task_name = f'({self.task_name}) ' if self.task_name else ''

        request_kwargs = self.get_request_kwargs()
        self._log(f"{task_name}{self._method} {self._url} with data: "
                  f"{request_kwargs if request_kwargs else 'None'}.")

        response = requests.request(self._method, self._url, **request_kwargs)

        self._log(f"{task_name}Status = {response.status_code}. "
                  f"Fetched = {len(response.content)} bytes.")
        return response.text


class HttpDestinationEndpoint(DestinationEndpointBase, HttpEndpointBase):

    def __init__(self, *args, **kwargs):
        super(DestinationEndpointBase, self).__init__(**kwargs)
        self._initialise(**kwargs)

    def push(self, content, **kwargs):
        print(content)
