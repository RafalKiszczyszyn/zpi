import pathlib
from feedreader.core.config import ClassConfig


BASE = pathlib.Path(__file__).resolve().parent.parent.parent
ENV = BASE / 'env' / 'test'
APPDATA = BASE / 'AppData'

"""
Application settings.
"""
CONFIG = {
    # Fetch feed every x seconds.
    'heartbeat': 5 * 60,     # 5 min

    # MongoDB database settings
    'database': {
        'connection_string': 'localhost',
        'database': 'feedreader',
        'collection': 'CachedArticles',
        'ttl': 5 * 60   # 5 minutes
    },

    # Event queue settings
    'event_queue': {
        'host': 'localhost',
        'vhost': '/',
        'username': 'guest',
        'password': 'guest',
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
