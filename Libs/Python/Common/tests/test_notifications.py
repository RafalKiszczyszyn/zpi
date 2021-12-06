from unittest import TestCase, mock

from zpi_common.services.notifications import TlsSecuredSmtpConnection


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
    pass