import pathlib
import sys; sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from contextlib import contextmanager
from unittest import TestCase, mock

from zpi_common.services.loggers import DevNullLogger, StdoutLogger
from zpi_common.services.notifications import TlsSecuredSmtpConnection, EmailBroadcastService


# noinspection PyMethodMayBeStatic
class TlsSecuredSmtpConnectionTests(TestCase):

    @mock.patch('smtplib.SMTP')
    @mock.patch('ssl.create_default_context')
    def test_Init_ConnectionIsOpened(self, sslContextMock, smtpMock):
        # Arrange
        contextMock = mock.Mock()
        sslContextMock.return_value = contextMock
        serverMock = mock.Mock()
        smtpMock.return_value = serverMock
        host, port = 'localhost', 333
        username, password = 'user', 'password'

        # Act
        TlsSecuredSmtpConnection(host, port, (username, password))

        # Assert
        sslContextMock.assert_called_once()
        smtpMock.assert_called_once_with(host, port)
        serverMock.starttls.assert_called_once_with(context=contextMock)
        serverMock.login.assrt_called_once_with(username, password)

    @mock.patch('smtplib.SMTP')
    @mock.patch('ssl.create_default_context')
    def test_Init_OpenedInsideWithStatement_ConnectionIsClosed(self, _, smtpMock):
        # Arrange
        serverMock = mock.Mock()
        smtpMock.return_value = serverMock
        host, port = 'localhost', 333
        username, password = 'user', 'password'

        # Act
        with TlsSecuredSmtpConnection(host, port, (username, password)):
            pass

        # Assert
        smtpMock.assert_called_once_with(host, port)
        serverMock.close.assert_called_once()


# noinspection PyMethodMayBeStatic
class EmailBroadcastServiceTests(TestCase):

    @contextmanager
    def getTempFile(self):
        import uuid
        import os

        template = str(uuid.uuid4())
        open(template, 'w').close()

        yield template

        os.remove(template)

    def test_Error_TemplateIsNotProvided_DefaultTemplateIsUsed(self):
        # Arrange
        credentials = ('user', 'password')
        recipients = ['example@example.com']
        connMock = mock.Mock()
        setattr(connMock, '__enter__', lambda *args, **kwargs: connMock)
        setattr(connMock, '__exit__', lambda *args, **kwargs: None)
        connFactoryMock = mock.Mock()
        connFactoryMock.create.return_value = connMock
        sut = EmailBroadcastService(
            connection_factory=connFactoryMock,
            credentials=credentials,
            recipients=recipients,
            templates=None,
            logger=DevNullLogger())

        title = 'Title'
        tags = {'message': 'Message', 'id': 1234}

        # Act
        sut.error(title=title, **tags)

        # Assert
        sender, recipients_, body = connMock.send_email.call_args[0]
        self.assertEqual(sender, credentials[0])
        self.assertSequenceEqual(recipients_, recipients)
        self.assertTrue(body.find('"message": "Message"') != -1)
        self.assertTrue(body.find('"id": 1234') != -1)

    def test_Info_TemplateIsProvided_TemplateIsUsed(self):
        # Arrange
        with self.getTempFile() as template:
            with open(template, 'w') as f:
                f.write('{{message}}, {{id}}')

            credentials = ('user', 'password')
            recipients = ['example@example.com']
            connMock = mock.Mock()
            setattr(connMock, '__enter__', lambda *args, **kwargs: connMock)
            setattr(connMock, '__exit__', lambda *args, **kwargs: None)
            connFactoryMock = mock.Mock()
            connFactoryMock.create.return_value = connMock
            sut = EmailBroadcastService(
                connection_factory=connFactoryMock,
                credentials=credentials,
                recipients=recipients,
                templates={EmailBroadcastService.INFO_TEMPLATE_NAME: template},
                logger=StdoutLogger())

            title = 'Title'
            tags = {'message': 'Message', 'id': 1234}

            # Act
            sut.info(title=title, **tags)

            # Assert
            sender, recipients_, body = connMock.send_email.call_args[0]
            self.assertEqual(sender, credentials[0])
            self.assertSequenceEqual(recipients_, recipients)
            self.assertTrue(body.find("Message, 1234") != -1)
