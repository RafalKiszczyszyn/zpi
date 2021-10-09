"""
Broker configuration file.
"""

# HTTP Server configuration
# Server is used to listen for events and send back the results
HOST = 'localhost'
PORT = 8080
EVENT_ENDPOINT = '/events'


"""Services which can be injected into task step implementations."""
SERVICES = {
    # Logger used for diagnosis
    # Is injected into all task step implementation by default.
    'LOGGER': {
        # Default logger implementation.
        # Prints logs into specified file.
        'class': 'broker.loggers.FileLogger',
        'args': {
            'filename': '../logs.txt'
        }
    }
}

"""List of tasks."""
TASKS = [
    {
        'name': 'Test Task',
        'steps': [
            {
                'name': 'Get data from polsat RSS',
                'class': 'broker.tasks.HttpGetTaskStep',
                'args': {'url': 'http://example.com'}
            },
            {
                'name': 'Post event in the queue',
                'class': 'broker.tasks.HttpPostTaskStep',
                'args': {'url': 'http://example.com'}
            }
        ]
    }
]
