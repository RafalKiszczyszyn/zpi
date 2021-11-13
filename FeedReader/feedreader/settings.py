import pathlib
from feedreader.core.config import Task, Class, Step


BASE = pathlib.Path(__file__).resolve().parent
APPDATA = BASE / 'appdata'

"""
Application settings.
"""
CONFIG = {
    # Fetch feed every x seconds.
    'heartbeat': 0,

    # MongoDB database settings
    'database': {
        'connection_string': 'mongodb://localhost:27017',
        'database': 'test',
        'collection': 'test',
        'ttl': 60
    },

    # Event queue settings
    'event_queue': {
        # 'url': 'amqp://guest:guest@localhost:5672/%2f?',
        'url': 'amqp://guest:guest@localhost:5671/%2f',
        'ssl': {
            'cafile': APPDATA / 'rabbitmq' / 'ca.pem',
            'certfile': APPDATA / 'rabbitmq' / 'feedreader.crt',
            'keyfile': APPDATA / 'rabbitmq' / 'feedreader.key'
        }
    }
}

EXECUTOR = Class(
    implementation='feedreader.app.tasks.FeedReader',
    args={'channel': 'feed'}
)

"""
List of tasks.
"""
TASKS = [
    Task(
        name='Polsat',
        steps=[
            Step(
                name='Parse',
                implementation='feedreader.app.tasks.RssParser',
                args={'url': 'https://www.polsatnews.pl/rss/polska.xml'}
            ),
            Step(
                name='Format',
                implementation='feedreader.app.tasks.RssConverter',
                args={'source': 'https://www.polsatnews.pl/rss/polska.xml'}
            )
        ]
    )
]
