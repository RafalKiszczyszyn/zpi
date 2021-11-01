"""
Application settings.
"""
CONFIG = {
    # Fetch feed every x seconds.
    'heartbeat': 3600,

    # Logger settings
    'logger': {
        'filename': '../logs.txt'
    },

    # Email notifications settings
    'email_notifications': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'credentials': {'username': 'example@outlook.com', 'password': 'password'},
        'template': '../appdata/email-template.html',
        'recipients': [
            '246655@student.pwr.edu.pl',
            'kiszczyszyn@gmail.com'
        ]
    },

    # Event queue settings
    'event_queue': {
        'url': 'amqp://guest:guest@localhost:5672/%2f?heartbeat=60',
        'channel': 'feed'
    }
}

"""
List of tasks.
"""
TASKS = [
    {
        'name': 'Polsat',
        'steps': [
            {
                'name': 'Parse',
                'class': 'feedreader.tasks.RssParser',
                'args': {
                    'url': 'https://www.polsatnews.pl/rss/polska.xml',
                }
            },
            {
                'name': 'Format',
                'class': 'feedreader.tasks.RssMapper',
            },
            {
                'name': 'Publish',
                'class': 'feedreader.tasks.QueueEventPublisher',
                'args': {
                    'channel': 'CHANNEL',
                }
            },
        ]
    }
]
