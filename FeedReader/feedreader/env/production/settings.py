import pathlib
from feedreader.core.config import ClassConfig

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
ENV = BASE / 'env' / 'production'
APPDATA = BASE / 'AppData'


"""
Application settings.
"""
CONFIG = {
    # Fetch feed every x seconds.
    'heartbeat': 30 * 60,     # 30 min

    # MongoDB database settings
    'database': {
        'connection_string': 'mongodb+srv://backend:backend@cluster0.pifu7.mongodb.net/ArticlesClassificationSystem?retryWrites=true&w=majority',
        'database': 'feedreader',
        'collection': 'CachedArticles',
        'ttl': 3 * 24 * 60 * 60   # 3 days
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

    # Email notifications settings
    'email_notifications': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'credentials': {
            'username': 'automated.kiszczyszyn@outlook.com',
            'password': 'zpi@outlook99'
        },
        'recipients': [
            '246655@student.pwr.edu.pl'
        ]
    }
}

SOURCES = BASE / 'sources.json'

MANAGEMENT_ENABLED = True
MANAGEMENT_HOST = 'localhost'
MANAGEMENT_PORT = 5000

EXECUTOR = ClassConfig(
    implementation='feedreader.service.tasks.FeedReader',
    args={'channel': 'feed'}
)
