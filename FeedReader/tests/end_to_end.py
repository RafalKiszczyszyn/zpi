from tests.utils import TestCase


class ExecuteTasksFromConfigTests(TestCase):

    class Service:
        pass

    class Config:

        SERVICES = {
            'TestService': 'tests.ExecuteTasksFromConfigTests.TestService'
        }

    pass