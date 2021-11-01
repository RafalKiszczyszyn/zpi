import smtplib
import ssl
from abc import abstractmethod, ABC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from feedreader import loggers


class EmailServiceException(Exception):
    pass


class EmailServiceBase(ABC):
    @abstractmethod
    def broadcast(self, title, message):
        pass


class AbstractSmtpConnection(ABC):
    @abstractmethod
    def connect(self, credentials):
        pass


class TlsSecuredSmtpConnection(AbstractSmtpConnection):

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._context = ssl.create_default_context()

    def connect(self, credentials):
        server = smtplib.SMTP(self._host, self._port)
        server.starttls(context=self._context)  # Secure the connection
        server.login(credentials['username'], credentials['password'])

        return server


class SmtpDebugConnection(AbstractSmtpConnection):

    def __init__(self, port):
        self._port = port

    def connect(self, credentials):
        server = smtplib.SMTP("localhost", self._port)
        server.ehlo()
        return server


class EmailService(EmailServiceBase):

    def __init__(self, credentials, recipients, template,
                 connection: AbstractSmtpConnection, logger: loggers.LoggerBase):
        self._credentials = credentials
        self._recipients = recipients
        self._template = template
        self._conn = connection
        self._logger = logger

    def broadcast(self, title, message):
        try:
            self._broadcast(title, message)
        except Exception as e:
            raise EmailServiceException(f"Sending email with title='{title}' failed.") from e

    def _broadcast(self, title, message):
        with self._conn.connect(credentials=self._credentials) as server:
            msg = MIMEMultipart()
            msg['From'] = self._credentials['username']
            msg['To'] = ', '.join(self._recipients)
            msg['Subject'] = title
            msg.attach(self._format_message(message))

            server.sendmail(self._credentials['username'], self._recipients, msg.as_string())

    def _format_message(self, message):
        placeholder = '{message}'
        try:
            with open(self._template, 'r') as template:
                content = template.read()
                if content.find(placeholder) == -1:
                    raise Exception(
                        f"Email message template='{self._template}' does not contain '{placeholder}' placeholder")

                content = content.format(content, message=message)
                return MIMEText(content, 'html')
        except Exception as e:
            self._log(f'Inserting message into template failed with error: {e}. Using plain text instead.')
            return MIMEText(message, 'text')

    def _log(self, content):
        self._logger.log(f"(Email Service) {content}")


def debug():
    service = EmailService(
        credentials={'username': 'username', 'password': 'password'},
        recipients=['example@example.com'],
        template='template.html',
        connection=SmtpDebugConnection(port=1000),
        logger=loggers.DebugLogger())

    service.broadcast('TITLE', 'MESSAGE')


def test_connection():
    password = input('Enter password:')
    service = EmailService(
        credentials={'username': 'automated.kiszczyszyn@outlook.com', 'password': password},
        recipients=['automated.kiszczyszyn.invalid@outlook.com'],
        template='template.html',
        connection=TlsSecuredSmtpConnection(host='smtp-mail.outlook.com', port=587),
        logger=loggers.DebugLogger())

    service.broadcast('TITLE', 'MESSAGE')


if __name__ == '__main__':
    # test_connection()
    debug()
