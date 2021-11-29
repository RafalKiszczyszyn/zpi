from __future__ import annotations

import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple, Dict, Union

from zpi_common.services.loggers import ILogger


class ISmtpConnection(ABC):

    @abstractmethod
    def __enter__(self) -> ISmtpConnection:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def send_email(self, sender: str, recipients: List[str], message: str):
        pass


class ISmtpConnectionFactory(ABC):

    @abstractmethod
    def create(self, credentials: Tuple[str, str]) -> ISmtpConnection:
        pass


class IEmailBroadcastService(ABC):

    @abstractmethod
    def error(self, title: str, **tags):
        pass

    @abstractmethod
    def info(self, title: str, **tags):
        pass


# --- IMPLEMENTATIONS ---


class TlsSecuredSmtpConnection(ISmtpConnection):

    def __init__(self, host: str, port: int, credentials: Tuple[str, str]):
        context = ssl.create_default_context()
        server = smtplib.SMTP(host, port)
        server.starttls(context=context)

        username, password = credentials
        server.login(username, password)

        self._server = server

    def __enter__(self) -> ISmtpConnection:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.close()

    def send_email(self, sender: str, recipients: List[str], message: str):
        self._server.sendmail(sender, recipients, message)


class TlsSecuredSmtpConnectionFactory(ISmtpConnectionFactory):

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port

    def create(self, credentials: Tuple[str, str]) -> ISmtpConnection:
        return TlsSecuredSmtpConnection(self._host, self._port, credentials)


class EmailBroadcastService(IEmailBroadcastService):

    @dataclass(frozen=True)
    class Template:
        name: str
        path: str

    ERROR_TEMPLATE_NAME: str = 'ERROR'
    INFO_TEMPLATE_NAME: str = 'INFO'

    def __init__(self,
                 connection_factory: ISmtpConnectionFactory,
                 credentials: Tuple[str, str],
                 recipients: List[str],
                 templates: Dict[str, str] = {},
                 logger: Union[ILogger, None] = None):
        self._credentials = credentials
        self._recipients = recipients
        self._connection_factory = connection_factory
        self._logger = logger

        self._templates: Dict[str, EmailBroadcastService.Template] = {}
        for name in templates:
            self._templates[name] = self.Template(name=name, path=templates[name])

    def error(self, title: str, **tags):
        self._with_formatted_message(template=self.ERROR_TEMPLATE_NAME, title=title, tags=tags)

    def info(self, title: str, **tags):
        self._with_formatted_message(template=self.INFO_TEMPLATE_NAME, title=title, tags=tags)

    def _with_formatted_message(self, template: str, title: str, tags: Dict[str, str]):
        message = self._from_template(template=template, tags=tags)
        plain = message is None
        if plain:
            self._warn('Using plain text instead')
            message = self._from_default(tags=tags)
        self._broadcast(title=title, message=message, plain=plain)

    def _broadcast(self, title: str, message: str, plain=False):
        with self._connection_factory.create(self._credentials) as connection:
            username, _ = self._credentials
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(self._recipients)
            msg['Subject'] = title
            msg.attach(MIMEText(message, 'html'))

            self._info(f"Sending email with title='{title}' to recipients={self._recipients}. Sender='{username}'")
            connection.send_email(username, self._recipients, msg.as_string())

    def _from_template(self, template: str, tags: Dict[str, str]) -> Union[str, None]:
        if template not in self._templates:
            self._warn(f"Template(name='{template}') is not provided")
            return None

        template_: EmailBroadcastService.Template = self._templates[template]
        try:
            with open(template_.path, 'r') as file:
                content = file.read()
        except IOError:
            self._warn(f"Could not load {template_}")
            return None

        for tag in tags:
            if content.find("{{" + tag + "}}") == -1:
                self._warn(f"{template_} does not contain tag={{{{{tag}}}}}")
                return None
            content = content.replace("{{" + tag + "}}", tags[tag])

        return content

    @staticmethod
    def _from_default(tags: Dict[str, str]) -> str:
        import json
        content = json.dumps(tags, indent=4, ensure_ascii=False, default=str)
        return f'<html><body><pre><code>{content}</code></pre></body></html>'

    def _info(self, info: str):
        if self._logger is not None:
            self._logger.info(info)

    def _warn(self, warning: str):
        if self._logger is not None:
            self._logger.warning(warning)
