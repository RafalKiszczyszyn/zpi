import smtplib

from debug import loggers
from feedreader.service.notifications import ISmtpConnection, EmailService


class SmtpDebugConnection(ISmtpConnection):

    def __init__(self, port):
        self._port = port

    def connect(self, credentials):
        server = smtplib.SMTP("localhost", self._port)
        server.ehlo()
        return server


def debug():
    # Start debugging server with command:
    # python -m smtpd -n -c DebuggingServer localhost:1000

    service = EmailService(
        credentials={'username': 'username', 'password': 'password'},
        recipients=['example@example.com'],
        template='../../AppData/traceback-template.html',
        connection=SmtpDebugConnection(port=1000),
        logger=loggers.DebugLogger())

    service.broadcast('Title', info='An exception occurred', traceback='traceback')