"""
Class name of logger implementation
"""
LOGGER = 'broker.logging.FileLogger'

"""
List of tasks.
"""
TASKS = [
    {
        "source": {
            "class": "broker.endpoints.HttpSourceEndpoint",
            "args": {
                'url': 'url', 'method': 'POST', 'params': ['params']
            }
        },
        "destination": {
            "class": "broker.endpoints.HttpDestinationEndpoint",
            "args": {
                'url': 'url', 'method': 'POST', 'params': ['params']
            }
        },
        "interceptors": ['broker.interceptors.Interceptor', 'broker.interceptors.Interceptor']
    }
]
