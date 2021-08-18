"""
Class name of logger implementation
"""
LOGGER = 'broker.loggers.FileLogger'

"""
List of tasks.
"""
TASKS = [
    {
        "name": "Test task",
        "source": {
            "class": "broker.endpoints.HttpSourceEndpoint",
            "args": {
                'url': 'https://api.github.com/events', 'method': 'GET'
            }
        },
        "destination": {
            "class": "broker.endpoints.HttpDestinationEndpoint",
            "args": {
                'url': 'url', 'method': 'POST', 'params': ['params']
            }
        }
    }
]
