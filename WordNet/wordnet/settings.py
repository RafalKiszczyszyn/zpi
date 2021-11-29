import pathlib

BASE = pathlib.Path(__file__).resolve().parent
APPDATA = BASE / 'AppData'

""" RabbitMQ Client Settings """
# Host
HOST = 'localhost'

# Virtual host
VHOST = 'main'

# Credentials
USERNAME = 'wordnet'
PASSWORD = 'wordnet'

# Exchange used to publish events. Should be named the same as the published resource
FANOUT = 'sentiments'

# Queue name prefix
QUEUE_NAME_PREFIX = 'wordnet'

# SSL
SSL_ENABLED = False
SSL_CA = APPDATA / 'ssl' / 'ca.pem'
SSL_CERT = APPDATA / 'ssl' / 'wordnet.crt'
SSL_KEY = APPDATA / 'ssl' / 'wordnet.key'

# If an exception occurs, sleep N minutes and restart
RESTART = 5 * 60

""" Nlp Service Settings """
CLARIN_USER = '246655@student.pwr.edu.pl'
CLARIN_WORKING_DIRECTORY = APPDATA / 'temp'

""" Notifications Settings """
NOTIFICATIONS_ENABLED = False
NOTIFICATIONS_USERNAME = 'automated.kiszczyszyn@outlook.com'
NOTIFICATIONS_PASSWORD = 'zpi@outlook99'
NOTIFICATIONS_RECIPIENTS = ['246655@student.pwr.edu.pl']
NOTIFICATIONS_HOST = 'smtp-mail.outlook.com'
NOTIFICATIONS_PORT = 587
