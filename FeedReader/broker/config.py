"""
FeedReader configuration file.
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
        'name': 'Polsat',
        'steps': [
            {
                'name': 'Parse',
                'class': 'broker.tasks.RssParser',
                'args': {
                    'url': 'https://www.polsatnews.pl/rss/polska.xml',
                }
            },
            {
                'name': 'Format',
                'class': 'broker.tasks.RssMapper',
            },
            {
                'name': 'Publish',
                'class': 'broker.tasks.QueueEventPublisher',
                'args': {
                    'channel': 'CHANNEL',
                }
            },
        ]
    }
]
