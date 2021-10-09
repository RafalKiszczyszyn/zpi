import requests
from abc import abstractmethod, ABC
from broker import core


class Task:

    class Meta:
        services = [core.InjectService(service_name='LOGGER', attribute_name='logger')]

    def __init__(self, context, steps):
        self.context = context
        self.steps = steps
        self.logger = None

    def log(self, content):
        if self.logger:
            self.logger.log(f'({self.context}) {content}')

    def execute(self):
        self.log('Started execution.')
        try:
            data = {}
            for step in self.steps:
                data = step.execute(data)
        except Exception as e:
            self.log(f'Error: {e}')
        self.log('Finished execution.')


class TaskStepBase(ABC):

    class Meta:
        services = [core.InjectService(service_name='LOGGER', attribute_name='logger')]

    def __init__(self, context, *args, **kwargs):
        self.context = context
        self.logger = None

    @abstractmethod
    def execute(self, data: dict) -> dict:
        pass

    def log(self, content):
        if self.logger:
            self.logger.log(f'({self.context}) {content}')


# ****************************************** IMPLEMENTATIONS ******************************************


class HttpGetTaskStep(TaskStepBase):

    class Meta:
        args = core.ConfigArgs(required=['url'], optional=['params'])

    def __init__(self, *args, **kwargs):
        super(HttpGetTaskStep, self).__init__(*args, **kwargs)
        self.url = None
        self.params = None

    def execute(self, data: dict) -> dict:
        self.log(f"HTTP GET {self.url} with params: {self.params if self.params else 'None'}.")

        response = requests.get(self.url, params=self.params)

        self.log(f"Status = {response.status_code}. Fetched = {len(response.content)} bytes.")

        return response.json()


class HttpPostTaskStep(TaskStepBase):

    class Meta:
        args = core.ConfigArgs(required=['url'], optional=['params'])

    def __init__(self, *args, **kwargs):
        super(HttpPostTaskStep, self).__init__(*args, **kwargs)
        self.url = None
        self.params = None

    def execute(self, data: dict) -> dict:
        self.log(f"HTTP POST {self.url} with params: {self.params if self.params else 'None'}.")

        response = requests.post(self.url, json=data, params=self.params)

        self.log(f"Status = {response.status_code}. Fetched = {len(response.content)} bytes.")

        return response.json()
