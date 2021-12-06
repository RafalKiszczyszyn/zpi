import pathlib
from feedreader.core.config import Task, Class, Step


BASE = pathlib.Path(__file__).resolve().parent
APPDATA = BASE / 'AppData'

"""
Application settings.
"""
CONFIG = {
    # Fetch feed every x seconds.
    'heartbeat': 2 * 60,     # 15 min

    # MongoDB database settings
    'database': {
        'connection_string': 'mongodb+srv://backend:backend@cluster0.pifu7.mongodb.net/ArticlesClassificationSystem?retryWrites=true&w=majority',
        'database': 'feedreader',
        'collection': 'CachedArticles',
        'ttl': 3*24*60*60   # 3 days
    },

    # Event queue settings
    'event_queue': {
        'host': 'rabbito',
        'vhost': 'main',
        'username': 'feedreader',
        'password': 'feedreader',
        'ssl': {
            'cafile': APPDATA / 'ssl' / 'ca.pem',
            'certfile': APPDATA / 'ssl' / 'feedreader.crt',
            'keyfile': APPDATA / 'ssl' / 'feedreader.key'
        }
    },
}

EXECUTOR = Class(
    implementation='feedreader.service.tasks.FeedReader',
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
                implementation='feedreader.service.tasks.RssParser',
                args={'url': 'https://www.polsatnews.pl/rss/polska.xml'}
            ),
            Step(
                name='Format',
                implementation='feedreader.service.tasks.RssConverter',
                args={'contentNodes': ['.news__description > p']}
            )
        ]
    )
]
