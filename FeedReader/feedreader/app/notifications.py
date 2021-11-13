import smtplib
import ssl
from abc import abstractmethod, ABC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from feedreader.app import loggers


class ISmtpConnection(ABC):
    @abstractmethod
    def connect(self, credentials):
        pass


class TlsSecuredSmtpConnection(ISmtpConnection):

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._context = ssl.create_default_context()

    def connect(self, credentials):
        server = smtplib.SMTP(self._host, self._port)
        server.starttls(context=self._context)  # Secure the connection
        server.login(credentials['username'], credentials['password'])

        return server


class EmailServiceException(Exception):
    pass


class IEmailService(ABC):
    @abstractmethod
    def broadcast(self, title, **tags):
        pass


class EmailService(IEmailService):

    def __init__(self, credentials, recipients, template,
                 connection: ISmtpConnection, logger: loggers.LoggerBase):
        self._credentials = credentials
        self._recipients = recipients
        self._template = template
        self._conn = connection
        self._logger = logger

    def broadcast(self, title, **tags):
        try:
            self._broadcast(title, tags)
        except Exception as e:
            raise EmailServiceException(f"Sending email with title='{title}' failed.") from e

    def _broadcast(self, title, tags):
        with self._conn.connect(credentials=self._credentials) as server:
            msg = MIMEMultipart()
            msg['From'] = self._credentials['username']
            msg['To'] = ', '.join(self._recipients)
            msg['Subject'] = title
            msg.attach(self._format_message(tags))

            server.sendmail(self._credentials['username'], self._recipients, msg.as_string())

    def _format_message(self, tags):
        try:
            with open(self._template, 'r') as template:
                content = template.read()
                for tag in tags:
                    if content.find(f"{{{{{tag}}}}}") == -1:
                        raise Exception(
                            f"Email message template='{self._template}' does not contain {{{{{tag}}}}} placeholder")
                    content = content.replace(f'{{{{{tag}}}}}', tags[tag])

                return MIMEText(content, 'html')
        except Exception as e:
            self._log(f'Inserting message into a template failed with error: {e}. Using plain text instead.')
            plain_message = "".join([tags[tag] + '\n' for tag in tags])
            return MIMEText(plain_message, 'text')

    def _log(self, content):
        self._logger.log(f"(Email Service) {content}")
